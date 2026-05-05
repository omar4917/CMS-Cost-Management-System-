"""
Database connection module for CMS Desktop App.
SQLite-only (portable/local usage).
"""

import os
import sys
import threading
import sqlite3
from dotenv import load_dotenv

# Load environment
if getattr(sys, 'frozen', False):
    app_dir = os.path.dirname(sys.executable)
else:
    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
load_dotenv(os.path.join(app_dir, '.env'))

DB_TYPE = "sqlite"

# GLOBALS
_conn = None
_table_columns_cache = {}
_schema_lock = threading.Lock()
_sqlite_initialized = False
_cash_transactions_ready = False
_project_profile_ready = False
DB_CONFIG = {}

def get_connection():
    global _conn
    if _conn is None:
        db_path = os.path.join(app_dir, "cms_data.db")
        _conn = sqlite3.connect(db_path, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _init_sqlite(_conn)
    return _conn

def _init_sqlite(conn):
    global _sqlite_initialized
    if _sqlite_initialized:
        return

    with _schema_lock:
        if _sqlite_initialized:
            return
        from core.schema_sqlite import init_sqlite_db

        init_sqlite_db(conn)
        _sqlite_initialized = True

def reset_connection_cache():
    """Reset connection and metadata caches."""
    global _conn, _sqlite_initialized, _cash_transactions_ready, _project_profile_ready
    if _conn:
        _conn.close()
    _conn = None
    _sqlite_initialized = False
    _cash_transactions_ready = False
    _project_profile_ready = False
    invalidate_table_columns()

def clear_database():
    """Truncate all tables in the current database, then re-seed defaults."""
    global _sqlite_initialized, _cash_transactions_ready, _project_profile_ready
    conn = get_connection()
    from core.schema_sqlite import clear_sqlite_db

    with _schema_lock:
        clear_sqlite_db(conn)
        invalidate_table_columns()
        _sqlite_initialized = True
        _cash_transactions_ready = False
        _project_profile_ready = False

def execute_query(query, params=None, fetch=True):
    """Execute a query and return results."""
    # Convert MySQL specific functions to SQLite equivalents
    if 'NOW()' in query:
        query = query.replace('NOW()', 'CURRENT_TIMESTAMP')
    if 'CURDATE()' in query:
        query = query.replace('CURDATE()', "date('now')")
        
    # Convert MySQL %s params to SQLite ? params if needed
    if '%s' in query and params:
        query = query.replace('%s', '?')
        
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
            
        if fetch:
            results = cursor.fetchall()
            # Convert sqlite3.Row to dict for compatibility
            return [dict(row) for row in results]
        
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()

def execute_many(query, data):
    """Execute a query for multiple rows."""
    if 'NOW()' in query:
        query = query.replace('NOW()', 'CURRENT_TIMESTAMP')
    if 'CURDATE()' in query:
        query = query.replace('CURDATE()', "date('now')")
        
    if '%s' in query and data:
        query = query.replace('%s', '?')

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.executemany(query, data)
        conn.commit()
        return cursor.rowcount
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()

def test_connection():
    """Test if database connection works."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        return True, "Connected successfully"
    except Exception as e:
        return False, str(e)

def get_table_columns(table_name):
    """Return a set of existing column names for a table."""
    cached = _table_columns_cache.get(table_name)
    if cached is not None:
        return cached

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f"PRAGMA table_info(`{table_name}`)")
        rows = cursor.fetchall()
        columns = {row['name'] for row in rows}

        _table_columns_cache[table_name] = columns
        return columns
    except Exception:
        return set()
    finally:
        cursor.close()

def get_existing_column(table_name, *candidates):
    """Return the first matching column name from candidates."""
    columns = get_table_columns(table_name)
    for candidate in candidates:
        if candidate in columns:
            return candidate
    return None

def has_table_column(table_name, column_name):
    return column_name in get_table_columns(table_name)

def invalidate_table_columns(table_name=None):
    """Clear cached table metadata."""
    if table_name:
        _table_columns_cache.pop(table_name, None)
    else:
        _table_columns_cache.clear()

def ensure_project_profile_columns():
    """Ensure project listing/profile columns exist for the desktop property showcase."""
    global _project_profile_ready
    if _project_profile_ready:
        return

    column_defs = {
        "property_type": "VARCHAR(120)",
        "property_for": "VARCHAR(50)",
        "construction_status": "VARCHAR(120)",
        "unit_size": "VARCHAR(120)",
        "transaction_type": "VARCHAR(80)",
        "floor_available_on": "VARCHAR(80)",
        "bedrooms": "VARCHAR(30)",
        "bathrooms": "VARCHAR(30)",
        "balconies": "VARCHAR(30)",
        "garages": "VARCHAR(50)",
        "furnishing": "VARCHAR(80)",
        "facing": "VARCHAR(80)",
        "features": "TEXT",
        "nearby_places": "TEXT",
        "corporate_office": "TEXT",
        "cover_image_path": "VARCHAR(500)",
    }

    with _schema_lock:
        if _project_profile_ready:
            return

        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(f"PRAGMA table_info(`projects`)")
            existing = {row["name"] for row in cursor.fetchall()}
            for column_name, definition in column_defs.items():
                if column_name not in existing:
                    try:
                        cursor.execute(f"ALTER TABLE `projects` ADD COLUMN `{column_name}` {definition}")
                    except Exception:
                        pass # Ignore if it fails in SQLite

            conn.commit()
            invalidate_table_columns("projects")
            _project_profile_ready = True
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()

def ensure_cash_transactions_table():
    """Create the portable transaction table if it does not already exist."""
    global _cash_transactions_ready
    if _cash_transactions_ready:
        return

    with _schema_lock:
        if _cash_transactions_ready:
            return

        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS cash_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INT NULL,
                    investor_id INT NULL,
                    contractor_id INT NULL,
                    entry_type VARCHAR(50) NOT NULL,
                    direction VARCHAR(10) NOT NULL,
                    amount DECIMAL(15,2) NOT NULL DEFAULT 0,
                    currency VARCHAR(10) DEFAULT 'BDT',
                    tx_date DATE NOT NULL,
                    counterparty VARCHAR(255) NULL,
                    reference_no VARCHAR(255) NULL,
                    payment_method VARCHAR(50) NULL,
                    status VARCHAR(50) DEFAULT 'confirmed',
                    source_table VARCHAR(50) DEFAULT 'manual',
                    source_id INT NULL,
                    notes TEXT NULL,
                    created_by INT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()
            invalidate_table_columns("cash_transactions")
            _cash_transactions_ready = True
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
