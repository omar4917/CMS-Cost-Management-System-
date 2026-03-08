"""
Database connection module for CMS Desktop App.
Supports both MySQL (for multi-user/networked usage) and SQLite (for offline/standalone).
"""

import os
import sys
import re
import threading
from dotenv import load_dotenv

# Load environment
if getattr(sys, 'frozen', False):
    app_dir = os.path.dirname(sys.executable)
else:
    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
load_dotenv(os.path.join(app_dir, '.env'))

DB_TYPE = os.getenv('DB_TYPE', 'mysql').lower()

# GLOBALS
_pool = None
_sqlite_initialized = False
_table_columns_cache = {}
_schema_lock = threading.Lock()
_cash_transactions_ready = False
_project_profile_ready = False
DB_CONFIG = {}


def _init_sqlite(conn):
    """Initialize SQLite schema if empty."""
    global _sqlite_initialized
    if _sqlite_initialized: return
    
    from core.schema_sqlite import init_sqlite_db
    init_sqlite_db(conn)
    _sqlite_initialized = True


if DB_TYPE == 'mysql':
    import pymysql
    import pymysql.cursors
    from dbutils.pooled_db import PooledDB

    DB_CONFIG = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 3306)),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASS', ''),
        'database': os.getenv('DB_NAME', 'cms_db'),
        'charset': 'utf8mb4',
        'autocommit': True,
        'cursorclass': pymysql.cursors.DictCursor
    }

    def get_pool():
        global _pool
        if _pool is None:
            _pool = PooledDB(
                creator=pymysql,
                maxconnections=5,
                mincached=2,
                maxcached=5,
                blocking=True,
                **DB_CONFIG
            )
        return _pool

    def get_connection():
        return get_pool().connection()

else:
    # SQLITE FALLBACK
    import sqlite3
    
    SQLITE_PATH = os.path.join(app_dir, os.getenv('DB_FILE', 'cms_local.db'))
    
    def dict_factory(cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    def get_connection():
        conn = sqlite3.connect(SQLITE_PATH, check_same_thread=False)
        conn.row_factory = dict_factory
        _init_sqlite(conn)
        return conn


def execute_query(query, params=None, fetch=True):
    """Execute a query and return results."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if DB_TYPE == 'sqlite':
            # SQLite uses ? instead of %s for bindings
            query = query.replace('%s', '?')
            query = re.sub(r'\bNOW\(\)', 'CURRENT_TIMESTAMP', query, flags=re.IGNORECASE)
            query = re.sub(r'\bCURDATE\(\)', "DATE('now')", query, flags=re.IGNORECASE)
            
        cursor.execute(query, params or ())
        
        if fetch:
            results = cursor.fetchall()
            return results
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


def execute_many(query, data):
    """Execute a query for multiple rows."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if DB_TYPE == 'sqlite':
            query = query.replace('%s', '?')
            query = re.sub(r'\bNOW\(\)', 'CURRENT_TIMESTAMP', query, flags=re.IGNORECASE)
            query = re.sub(r'\bCURDATE\(\)', "DATE('now')", query, flags=re.IGNORECASE)
            
        cursor.executemany(query, data)
        conn.commit()
        return cursor.rowcount
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


def test_connection():
    """Test if database connection works."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()
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
        if DB_TYPE == 'sqlite':
            cursor.execute(f"PRAGMA table_info({table_name})")
            rows = cursor.fetchall()
            columns = {row['name'] for row in rows}
        else:
            cursor.execute(f"SHOW COLUMNS FROM `{table_name}`")
            rows = cursor.fetchall()
            columns = {row['Field'] for row in rows}

        _table_columns_cache[table_name] = columns
        return columns
    except Exception:
        return set()
    finally:
        cursor.close()
        conn.close()


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
            if DB_TYPE == "sqlite":
                cursor.execute("PRAGMA table_info(projects)")
                existing = {row["name"] for row in cursor.fetchall()}
                for column_name, definition in column_defs.items():
                    if column_name not in existing:
                        cursor.execute(f"ALTER TABLE projects ADD COLUMN {column_name} {definition}")
            else:
                cursor.execute("SHOW COLUMNS FROM `projects`")
                existing = {row["Field"] for row in cursor.fetchall()}
                for column_name, definition in column_defs.items():
                    if column_name not in existing:
                        cursor.execute(f"ALTER TABLE `projects` ADD COLUMN `{column_name}` {definition}")

            conn.commit()
            invalidate_table_columns("projects")
            _project_profile_ready = True
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()


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
            if DB_TYPE == "sqlite":
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS cash_transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        project_id INTEGER,
                        investor_id INTEGER,
                        contractor_id INTEGER,
                        entry_type VARCHAR(50) NOT NULL,
                        direction VARCHAR(10) NOT NULL,
                        amount DECIMAL(15,2) NOT NULL DEFAULT 0,
                        currency VARCHAR(10) DEFAULT 'BDT',
                        tx_date DATE NOT NULL,
                        counterparty VARCHAR(255),
                        reference_no VARCHAR(255),
                        payment_method VARCHAR(50),
                        status VARCHAR(50) DEFAULT 'confirmed',
                        source_table VARCHAR(50) DEFAULT 'manual',
                        source_id INTEGER,
                        notes TEXT,
                        created_by INTEGER,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
            else:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS cash_transactions (
                        id INT AUTO_INCREMENT PRIMARY KEY,
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
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
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
            conn.close()
