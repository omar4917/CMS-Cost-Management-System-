"""
SQLite Schema definition for CMS Desktop App.
Used when the application runs in local/offline mode without MySQL.
"""

import sqlite3

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    password VARCHAR(255) NOT NULL,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'admin',
    investor_id INTEGER,
    avatar VARCHAR(255),
    is_active BOOLEAN DEFAULT 1,
    last_login DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    location VARCHAR(255),
    type VARCHAR(50),
    property_type VARCHAR(120),
    property_for VARCHAR(50),
    status VARCHAR(50) DEFAULT 'planning',
    construction_status VARCHAR(120),
    start_date DATE,
    estimated_end_date DATE,
    actual_end_date DATE,
    total_budget DECIMAL(15,2) DEFAULT 0,
    progress DECIMAL(5,2) DEFAULT 0,
    unit_size VARCHAR(120),
    transaction_type VARCHAR(80),
    floor_available_on VARCHAR(80),
    bedrooms VARCHAR(30),
    bathrooms VARCHAR(30),
    balconies VARCHAR(30),
    garages VARCHAR(50),
    total_floors INTEGER,
    total_units INTEGER,
    furnishing VARCHAR(80),
    facing VARCHAR(80),
    land_area VARCHAR(100),
    building_area VARCHAR(100),
    features TEXT,
    nearby_places TEXT,
    corporate_office TEXT,
    cover_image_path VARCHAR(500),
    created_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cost_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    icon VARCHAR(50),
    description TEXT,
    is_default BOOLEAN DEFAULT 1,
    parent_id INTEGER,
    sort_order INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cost_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    category_id INTEGER,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    quantity DECIMAL(15,2) DEFAULT 0,
    unit VARCHAR(50),
    unit_price DECIMAL(15,2) DEFAULT 0,
    estimated_amount DECIMAL(15,2) DEFAULT 0,
    actual_amount DECIMAL(15,2) DEFAULT 0,
    currency VARCHAR(10) DEFAULT 'BDT',
    date DATE,
    vendor VARCHAR(255),
    invoice_no VARCHAR(100),
    status VARCHAR(50) DEFAULT 'pending',
    notes TEXT,
    created_by INTEGER,
    approved_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY(category_id) REFERENCES cost_categories(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS investor_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    color VARCHAR(50) DEFAULT '#3b82f6',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS investors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    address TEXT,
    type_id INTEGER,
    company VARCHAR(255),
    company_designation VARCHAR(255),
    national_id VARCHAR(50),
    bank_name VARCHAR(255),
    bank_account VARCHAR(255),
    is_active BOOLEAN DEFAULT 1,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(type_id) REFERENCES investor_types(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS investments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    investor_id INTEGER,
    project_id INTEGER,
    amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'BDT',
    date DATE,
    payment_method VARCHAR(50),
    reference_no VARCHAR(255),
    status VARCHAR(50) DEFAULT 'confirmed',
    notes TEXT,
    created_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(investor_id) REFERENCES investors(id) ON DELETE CASCADE,
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS payment_schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    investor_id INTEGER,
    project_id INTEGER,
    installment_no INTEGER,
    amount DECIMAL(15,2) NOT NULL,
    due_date DATE NOT NULL,
    paid_date DATE,
    paid_amount DECIMAL(15,2) DEFAULT 0,
    status VARCHAR(50) DEFAULT 'pending',
    reminder_sent BOOLEAN DEFAULT 0,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(investor_id) REFERENCES investors(id) ON DELETE CASCADE,
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
);

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
);

CREATE TABLE IF NOT EXISTS email_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    investor_id INTEGER,
    to_email VARCHAR(255) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    status VARCHAR(50) NOT NULL,
    error TEXT,
    sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(investor_id) REFERENCES investors(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS email_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    is_system BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS contractors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    company VARCHAR(255),
    specialization VARCHAR(255),
    address TEXT,
    rating DECIMAL(2,1) DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS contractor_payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contractor_id INTEGER,
    project_id INTEGER,
    amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'BDT',
    date DATE NOT NULL,
    invoice_no VARCHAR(255),
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    notes TEXT,
    created_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(contractor_id) REFERENCES contractors(id) ON DELETE CASCADE,
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action VARCHAR(50) NOT NULL,
    description TEXT,
    entity_type VARCHAR(50),
    entity_id INTEGER,
    old_values TEXT,
    new_values TEXT,
    ip_address VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    file_path VARCHAR(255) NOT NULL,
    file_type VARCHAR(50),
    entity_type VARCHAR(50),
    entity_id INTEGER,
    uploaded_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(uploaded_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS currencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(50),
    symbol VARCHAR(10),
    exchange_rate_to_base DECIMAL(15,6) DEFAULT 1.0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    category VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""

# Default Seed Data
COST_CATEGORIES = [
    ("Land Acquisition & Registration", "🗺️", "Costs related to buying and registering the land"),
    ("Construction (Materials, Labor, Equipment, Machinery Rental)", "🏗️", "Core construction and labor costs"),
    ("Architectural & Engineering Fees", "📐", "Design, structural, and architectural consulting"),
    ("Interior Design & Finishing", "🎨", "Interior decor, paint, tiles, etc."),
    ("Electrical, Plumbing & HVAC", "⚡", "Wiring, piping, air conditioning"),
    ("Elevator/Lift Installation", "🛗", "Elevator purchase and installation"),
    ("Fire Safety & Security Systems", "🧯", "Fire alarms, extinguishers, CCTV, access control"),
    ("Legal Fees & Documentation", "⚖️", "Lawyer fees, contract drafting, notary"),
    ("Government Permits & Licenses", "📜", "RAJUK/City Corp approvals, environmental permits"),
    ("Taxes & Duties (VAT, Capital Gains, Stamp Duty)", "🏛️", "All local and national taxes"),
    ("Insurance (Construction + Property)", "🛡️", "Insurance coverage during and after construction"),
    ("Marketing & Sales (Brochures, Ads, Commission)", "📢", "Sales commissions, advertising, branding"),
    ("Utility Connections (Gas, Water, Electricity, Internet)", "🚰", "WASA, DESCO, Titas Gas connections"),
    ("Landscaping & Exterior Work", "🌳", "Gardens, pathways, boundary walls"),
    ("Parking & Common Area Development", "🚗", "Basement parking, lobby, gym, pool setup"),
    ("Infrastructure (Roads, Drainage, Sewage)", "🛣️", "Connecting roads to main avenues, heavy drainage"),
    ("Environmental Compliance & Soil Testing", "🧪", "Soil reports, environmental impact assessments"),
    ("Demolition Costs", "🏚️", "Knocking down old structures on site"),
    ("Project Management & Supervision Fees", "👔", "Site engineer and supervisor salaries/fees"),
    ("Financing Costs (Loan Interest, Bank Charges)", "🏦", "Interest on bank loans and processing fees"),
    ("Contingency Fund", "🚑", "Emergency reserve for unexpected overruns"),
    ("Furniture & Fixtures (if furnished units)", "🛋️", "Ready flat furnishings, lobby furniture"),
    ("Transportation & Logistics", "🚛", "Moving materials to and from site"),
    ("Consultant & Advisory Fees", "💼", "Third party consulting outside of engineering"),
    ("Property Management Setup", "🏢", "Software, initial HOA setup, security hiring"),
    ("Raw Material: Land", "🌍", "Specific land parcels"),
    ("Raw Material: Bricks", "🧱", "Red bricks, hollow blocks"),
    ("Raw Material: Rod/Steel", "⛓️", "TMT bars, steel structures"),
    ("Raw Material: Sand", "⏳", "Sylhet sand, local sand"),
    ("Raw Material: Labour", "👷", "Daily wages, contracted labor"),
    ("Raw Material: Stone", "🪨", "Crushed stone, boulder"),
    ("Raw Material: Glass", "🪟", "Windows, facades"),
    ("Raw Material: Furniture", "🪑", "Woodwork, cabinets"),
    ("Raw Material: Wood", "🪵", "Doors, frames, formwork"),
]

INVESTOR_TYPES = [
    ("Owner", "Land owner or primary equity holder", "#3b82f6"),
    ("Partner", "Joint venture business partner", "#10b981"),
    ("Flat Buyer", "Purchasing a specific apartment", "#8b5cf6"),
    ("Building Buyer", "Purchasing the entire commercial/residential building", "#f59e0b"),
    ("Corporate", "Institutional investor or company", "#ef4444"),
]

DEFAULT_ADMIN_HASH = "$2b$12$LKYU0xHwEGhXWOtwfamBeebJGQ5IF2fdhhDYzIXQS55AP1crApGmS"
LEGACY_ADMIN_HASH = "$2a$10$7Z8l6U5/1hIqy6vOqZ/CbuR30x6JkXF/mZg2x1v1L.6/w1B1.V8gO"


def _table_columns(cursor, table_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = set()
    for row in cursor.fetchall():
        if isinstance(row, dict):
            columns.add(row["name"])
        else:
            columns.add(row[1])
    return columns


def _ensure_column(cursor, table_name, column_name, definition):
    if column_name not in _table_columns(cursor, table_name):
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")


def _scalar(row, key):
    if isinstance(row, dict):
        return row[key]
    return row[0]


def _run_migrations(cursor):
    _ensure_column(cursor, "users", "password", "VARCHAR(255)")
    _ensure_column(cursor, "users", "first_name", "VARCHAR(255)")
    _ensure_column(cursor, "users", "last_name", "VARCHAR(255)")
    _ensure_column(cursor, "users", "investor_id", "INTEGER")
    _ensure_column(cursor, "users", "last_login", "DATETIME")

    user_columns = _table_columns(cursor, "users")
    if "password_hash" in user_columns:
        cursor.execute("UPDATE users SET password = COALESCE(password, password_hash) WHERE password IS NULL OR password = ''")

    _ensure_column(cursor, "projects", "estimated_end_date", "DATE")
    _ensure_column(cursor, "projects", "total_floors", "INTEGER")
    _ensure_column(cursor, "projects", "total_units", "INTEGER")
    _ensure_column(cursor, "projects", "land_area", "VARCHAR(100)")
    _ensure_column(cursor, "projects", "building_area", "VARCHAR(100)")
    _ensure_column(cursor, "projects", "property_type", "VARCHAR(120)")
    _ensure_column(cursor, "projects", "property_for", "VARCHAR(50)")
    _ensure_column(cursor, "projects", "construction_status", "VARCHAR(120)")
    _ensure_column(cursor, "projects", "unit_size", "VARCHAR(120)")
    _ensure_column(cursor, "projects", "transaction_type", "VARCHAR(80)")
    _ensure_column(cursor, "projects", "floor_available_on", "VARCHAR(80)")
    _ensure_column(cursor, "projects", "bedrooms", "VARCHAR(30)")
    _ensure_column(cursor, "projects", "bathrooms", "VARCHAR(30)")
    _ensure_column(cursor, "projects", "balconies", "VARCHAR(30)")
    _ensure_column(cursor, "projects", "garages", "VARCHAR(50)")
    _ensure_column(cursor, "projects", "furnishing", "VARCHAR(80)")
    _ensure_column(cursor, "projects", "facing", "VARCHAR(80)")
    _ensure_column(cursor, "projects", "features", "TEXT")
    _ensure_column(cursor, "projects", "nearby_places", "TEXT")
    _ensure_column(cursor, "projects", "corporate_office", "TEXT")
    _ensure_column(cursor, "projects", "cover_image_path", "VARCHAR(500)")
    _ensure_column(cursor, "projects", "created_by", "INTEGER")

    _ensure_column(cursor, "investors", "national_id", "VARCHAR(50)")

    project_columns = _table_columns(cursor, "projects")
    if "est_end_date" in project_columns:
        cursor.execute(
            "UPDATE projects SET estimated_end_date = COALESCE(estimated_end_date, est_end_date) "
            "WHERE est_end_date IS NOT NULL"
        )

    _ensure_column(cursor, "cost_items", "invoice_no", "VARCHAR(100)")
    _ensure_column(cursor, "cost_items", "approved_by", "INTEGER")

    _ensure_column(cursor, "payment_schedules", "installment_no", "INTEGER")
    _ensure_column(cursor, "payment_schedules", "paid_amount", "DECIMAL(15,2) DEFAULT 0")

    _ensure_column(cursor, "contractors", "address", "TEXT")
    _ensure_column(cursor, "contractors", "notes", "TEXT")

    _ensure_column(cursor, "contractor_payments", "date", "DATE")
    _ensure_column(cursor, "contractor_payments", "notes", "TEXT")
    _ensure_column(cursor, "contractor_payments", "created_by", "INTEGER")

    contractor_payment_columns = _table_columns(cursor, "contractor_payments")
    if "payment_date" in contractor_payment_columns:
        cursor.execute(
            "UPDATE contractor_payments SET date = COALESCE(date, payment_date) "
            "WHERE payment_date IS NOT NULL"
        )

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

def init_sqlite_db(conn):
    """Run migrations and seed the database if it is empty."""
    cursor = conn.cursor()
    
    # Create tables
    cursor.executescript(SCHEMA_SQL)
    _run_migrations(cursor)
    
    # Check if admin user exists
    cursor.execute("SELECT id, password FROM users WHERE username='admin'")
    admin_row = cursor.fetchone()
    if not admin_row:
        cursor.execute(
            "INSERT INTO users (username, password, first_name, last_name, role) "
            "VALUES ('admin', ?, 'System', 'Admin', 'superadmin')",
            (DEFAULT_ADMIN_HASH,),
        )
    else:
        current_hash = admin_row["password"] if isinstance(admin_row, dict) else admin_row[1]
        if current_hash == LEGACY_ADMIN_HASH:
            cursor.execute("UPDATE users SET password=? WHERE username='admin'", (DEFAULT_ADMIN_HASH,))
    
    # Check if categories exist
    cursor.execute("SELECT COUNT(*) FROM cost_categories")
    if _scalar(cursor.fetchone(), "COUNT(*)") == 0:
        for idx, (name, icon, desc) in enumerate(COST_CATEGORIES):
            cursor.execute("INSERT INTO cost_categories (name, icon, description, sort_order) VALUES (?, ?, ?, ?)", 
                          (name, icon, desc, idx * 10))
                          
    # Check if investor types exist
    cursor.execute("SELECT COUNT(*) FROM investor_types")
    if _scalar(cursor.fetchone(), "COUNT(*)") == 0:
        for name, desc, color in INVESTOR_TYPES:
            cursor.execute("INSERT INTO investor_types (name, description, color) VALUES (?, ?, ?)", 
                          (name, desc, color))
                          
    # Check if email templates exist
    cursor.execute("SELECT COUNT(*) FROM email_templates")
    if _scalar(cursor.fetchone(), "COUNT(*)") == 0:
        templates = [
            ("Welcome to CMS", "Welcome to our Project '{project}'", "Dear {name},\n\nWelcome aboard! We are thrilled to have you as a valued {type} in our project '{project}'.\n\nYour portal access will be granted shortly.\n\nBest Regards,\nThe Management Team", 1),
            ("Investment Received", "Receipt for Payment: ৳{amount}", "Dear {name},\n\nThis is to confirm that we have successfully received your payment of ৳{amount} on {date} for the project '{project}'.\n\nThank you for your continued trust and investment.\n\nBest Regards,\nFinance Department", 1),
            ("Payment Overdue Reminder", "ACTION REQUIRED: Overdue Payment for '{project}'", "Dear {name},\n\nThis is a gentle reminder that your scheduled payment of ৳{amount} for the project '{project}' was due on {date} and is currently marked as overdue.\n\nPlease arrange for payment as soon as possible to avoid any project delays.\n\nBest Regards,\nFinance Department", 1)
        ]
        for name, subj, body, sys in templates:
            cursor.execute("INSERT INTO email_templates (name, subject, body, is_system) VALUES (?, ?, ?, ?)",
                          (name, subj, body, sys))
            
    # Default Settings
    cursor.execute("SELECT COUNT(*) FROM settings")
    if _scalar(cursor.fetchone(), "COUNT(*)") == 0:
        settings = [
            ("currency_base", "BDT", "financial"),
            ("currency_symbol", "৳", "financial"),
            ("tax_rate", "15", "financial")
        ]
        for key, val, cat in settings:
            cursor.execute("INSERT INTO settings (setting_key, setting_value, category) VALUES (?, ?, ?)",
                          (key, val, cat))
                          
    # Check if currencies exist
    cursor.execute("SELECT COUNT(*) FROM currencies")
    if _scalar(cursor.fetchone(), "COUNT(*)") == 0:
        currencies = [
            ("BDT", "Bangladeshi Taka", "৳", 1.0),
            ("USD", "US Dollar", "$", 0.0085),
            ("EUR", "Euro", "€", 0.0078),
            ("GBP", "British Pound", "£", 0.0067)
        ]
        for c, n, s, r in currencies:
            cursor.execute("INSERT INTO currencies (code, name, symbol, exchange_rate_to_base) VALUES (?, ?, ?, ?)",
                          (c, n, s, r))
                          
    conn.commit()
