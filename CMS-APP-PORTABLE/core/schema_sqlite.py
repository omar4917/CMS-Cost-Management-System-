"""
SQLite schema + seed data for the CMS Desktop App.

The app initializes required tables + baseline seed data on first connection.
"""

from __future__ import annotations

from typing import Iterable


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

# bcrypt hash for "admin123"
DEFAULT_ADMIN_HASH = "$2b$12$XJJag9r3PeyWdKKNZne8/O5.YEUWuqYawk5Z9h3mlA09h5ljL1rYW"
LEGACY_ADMIN_HASH = "$2a$10$7Z8l6U5/1hIqy6vOqZ/CbuR30x6JkXF/mZg2x1v1L.6/w1B1.V8gO"


def _first_value(row):
    if row is None:
        return None
    try:
        # For sqlite3.Row dict-like access
        return row[0]
    except Exception:
        return None


def _table_columns(cursor, table_name: str) -> set[str]:
    cursor.execute(f"PRAGMA table_info(`{table_name}`)")
    rows = cursor.fetchall() or []
    columns = set()
    for row in rows:
        columns.add(row["name"])
    return columns


def _ensure_column(cursor, table_name: str, column_name: str, definition: str) -> None:
    if column_name not in _table_columns(cursor, table_name):
        try:
            cursor.execute(f"ALTER TABLE `{table_name}` ADD COLUMN `{column_name}` {definition}")
        except Exception:
            pass # SQLite has limited ALTER TABLE support, so some defaults might fail if not handled well


def _create_tables(cursor) -> None:
    # NOTE: Keep tables permissive (nullable)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS `users` (
            `id` INTEGER PRIMARY KEY AUTOINCREMENT,
            `username` VARCHAR(255) NOT NULL UNIQUE,
            `email` VARCHAR(255) NULL UNIQUE,
            `password` VARCHAR(255) NOT NULL,
            `first_name` VARCHAR(255) NULL,
            `last_name` VARCHAR(255) NULL,
            `role` VARCHAR(50) DEFAULT 'admin',
            `investor_id` INT NULL,
            `avatar` VARCHAR(255) NULL,
            `is_active` TINYINT(1) DEFAULT 1,
            `last_login` DATETIME NULL,
            `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS `projects` (
            `id` INTEGER PRIMARY KEY AUTOINCREMENT,
            `name` VARCHAR(255) NOT NULL,
            `description` TEXT NULL,
            `location` VARCHAR(255) NULL,
            `type` VARCHAR(50) NULL,
            `property_type` VARCHAR(120) NULL,
            `property_for` VARCHAR(50) NULL,
            `status` VARCHAR(50) DEFAULT 'planning',
            `construction_status` VARCHAR(120) NULL,
            `start_date` DATE NULL,
            `estimated_end_date` DATE NULL,
            `actual_end_date` DATE NULL,
            `total_budget` DECIMAL(15,2) DEFAULT 0,
            `progress` DECIMAL(5,2) DEFAULT 0,
            `unit_size` VARCHAR(120) NULL,
            `transaction_type` VARCHAR(80) NULL,
            `floor_available_on` VARCHAR(80) NULL,
            `bedrooms` VARCHAR(30) NULL,
            `bathrooms` VARCHAR(30) NULL,
            `balconies` VARCHAR(30) NULL,
            `garages` VARCHAR(50) NULL,
            `total_floors` INT NULL,
            `total_units` INT NULL,
            `furnishing` VARCHAR(80) NULL,
            `facing` VARCHAR(80) NULL,
            `land_area` VARCHAR(100) NULL,
            `building_area` VARCHAR(100) NULL,
            `features` TEXT NULL,
            `nearby_places` TEXT NULL,
            `corporate_office` TEXT NULL,
            `cover_image_path` VARCHAR(500) NULL,
            `created_by` INT NULL,
            `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS `cost_categories` (
            `id` INTEGER PRIMARY KEY AUTOINCREMENT,
            `name` VARCHAR(255) NOT NULL,
            `icon` VARCHAR(50) NULL,
            `description` TEXT NULL,
            `is_default` TINYINT(1) DEFAULT 1,
            `parent_id` INT NULL,
            `sort_order` INT DEFAULT 0,
            `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS `cost_items` (
            `id` INTEGER PRIMARY KEY AUTOINCREMENT,

            `name` VARCHAR(300) NULL,
            `project_id` INT NULL,
            `category_id` INT NULL,
            `description` VARCHAR(500) NULL,
            `quantity` DECIMAL(15,2) DEFAULT 0,
            `unit` VARCHAR(50) NULL,
            `unit_price` DECIMAL(15,2) DEFAULT 0,
            `estimated_amount` DECIMAL(15,2) DEFAULT 0,
            `actual_amount` DECIMAL(15,2) DEFAULT 0,
            `currency` VARCHAR(10) DEFAULT 'BDT',
            `date` DATE NULL,
            `vendor` VARCHAR(200) NULL,
            `invoice_no` VARCHAR(255) NULL,
            `status` VARCHAR(50) NULL,
            `notes` TEXT NULL,
            `created_by` INT NULL,
            `approved_by` INT NULL,

            `receive_date` DATE NULL,
            `receive_detail` VARCHAR(255) NULL,
            `receive_amount` DECIMAL(15,2) DEFAULT 0,
            `received_from` VARCHAR(255) NULL,
            `cost_date` DATE NULL,
            `cost_detail` VARCHAR(300) NULL,
            `cost_amount` DECIMAL(15,2) DEFAULT 0,
            `pay_to` VARCHAR(255) NULL,
            `unit_rate` DECIMAL(15,2) DEFAULT 0,
            `qty` DECIMAL(15,2) DEFAULT 0,
            `qty_cft` DECIMAL(15,2) DEFAULT 0,
            `remarks` TEXT NULL,
            `cost_head_materials` VARCHAR(255) NULL,
            `structure_or_finishing` VARCHAR(50) NULL,
            `cost_summary_1` VARCHAR(255) NULL,
            `category_boq_mapping` VARCHAR(255) NULL,
            `cost_head_floors` VARCHAR(255) NULL,
            `cost_head_project` VARCHAR(255) NULL,
            `cost_head_months` VARCHAR(50) NULL,

            `extra_1` TEXT NULL,
            `extra_2` TEXT NULL,
            `extra_3` TEXT NULL,
            `extra_4` TEXT NULL,
            `extra_5` TEXT NULL,
            `extra_6` TEXT NULL,
            `extra_7` TEXT NULL,
            `extra_8` TEXT NULL,
            `extra_9` TEXT NULL,
            `extra_10` TEXT NULL,

            `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS `custom_field_labels` (
            `id` INTEGER PRIMARY KEY AUTOINCREMENT,
            `project_id` INT NOT NULL,
            `field_key` VARCHAR(50) NOT NULL,
            `label` VARCHAR(255) NOT NULL,
            `sort_order` INT DEFAULT 0,
            `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS `investor_types` (
            `id` INTEGER PRIMARY KEY AUTOINCREMENT,
            `name` VARCHAR(255) NOT NULL,
            `description` TEXT NULL,
            `color` VARCHAR(50) DEFAULT '#3b82f6',
            `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS `investors` (
            `id` INTEGER PRIMARY KEY AUTOINCREMENT,
            `name` VARCHAR(255) NOT NULL,
            `email` VARCHAR(255) NULL,
            `phone` VARCHAR(50) NULL,
            `address` TEXT NULL,
            `type_id` INT NULL,
            `company` VARCHAR(255) NULL,
            `company_designation` VARCHAR(255) NULL,
            `national_id` VARCHAR(50) NULL,
            `bank_name` VARCHAR(255) NULL,
            `bank_account` VARCHAR(255) NULL,
            `is_active` TINYINT(1) DEFAULT 1,
            `notes` TEXT NULL,
            `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS `investments` (
            `id` INTEGER PRIMARY KEY AUTOINCREMENT,
            `investor_id` INT NULL,
            `project_id` INT NULL,
            `amount` DECIMAL(15,2) NOT NULL,
            `currency` VARCHAR(10) DEFAULT 'BDT',
            `date` DATE NULL,
            `payment_method` VARCHAR(50) NULL,
            `reference_no` VARCHAR(255) NULL,
            `status` VARCHAR(50) DEFAULT 'confirmed',
            `notes` TEXT NULL,
            `created_by` INT NULL,
            `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS `payment_schedules` (
            `id` INTEGER PRIMARY KEY AUTOINCREMENT,
            `investor_id` INT NULL,
            `project_id` INT NULL,
            `installment_no` INT NULL,
            `amount` DECIMAL(15,2) NOT NULL,
            `due_date` DATE NOT NULL,
            `paid_date` DATE NULL,
            `paid_amount` DECIMAL(15,2) DEFAULT 0,
            `status` VARCHAR(50) DEFAULT 'pending',
            `reminder_sent` TINYINT(1) DEFAULT 0,
            `notes` TEXT NULL,
            `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS `cash_transactions` (
            `id` INTEGER PRIMARY KEY AUTOINCREMENT,
            `project_id` INT NULL,
            `investor_id` INT NULL,
            `contractor_id` INT NULL,
            `entry_type` VARCHAR(50) NOT NULL,
            `direction` VARCHAR(10) NOT NULL,
            `amount` DECIMAL(15,2) NOT NULL DEFAULT 0,
            `currency` VARCHAR(10) DEFAULT 'BDT',
            `tx_date` DATE NOT NULL,
            `counterparty` VARCHAR(255) NULL,
            `reference_no` VARCHAR(255) NULL,
            `payment_method` VARCHAR(50) NULL,
            `status` VARCHAR(50) DEFAULT 'confirmed',
            `source_table` VARCHAR(50) DEFAULT 'manual',
            `source_id` INT NULL,
            `notes` TEXT NULL,
            `created_by` INT NULL,
            `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS `email_logs` (
            `id` INTEGER PRIMARY KEY AUTOINCREMENT,
            `investor_id` INT NULL,
            `to_email` VARCHAR(255) NOT NULL,
            `subject` VARCHAR(255) NOT NULL,
            `body` TEXT NOT NULL,
            `status` VARCHAR(50) NOT NULL,
            `error` TEXT NULL,
            `sent_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS `email_templates` (
            `id` INTEGER PRIMARY KEY AUTOINCREMENT,
            `name` VARCHAR(255) NOT NULL,
            `subject` VARCHAR(255) NOT NULL,
            `body` TEXT NOT NULL,
            `is_system` TINYINT(1) DEFAULT 0,
            `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS `contractors` (
            `id` INTEGER PRIMARY KEY AUTOINCREMENT,
            `name` VARCHAR(255) NOT NULL,
            `email` VARCHAR(255) NULL,
            `phone` VARCHAR(50) NULL,
            `company` VARCHAR(255) NULL,
            `specialization` VARCHAR(255) NULL,
            `address` TEXT NULL,
            `rating` DECIMAL(2,1) DEFAULT 0,
            `is_active` TINYINT(1) DEFAULT 1,
            `notes` TEXT NULL,
            `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS `contractor_payments` (
            `id` INTEGER PRIMARY KEY AUTOINCREMENT,
            `contractor_id` INT NULL,
            `project_id` INT NULL,
            `amount` DECIMAL(15,2) NOT NULL,
            `currency` VARCHAR(10) DEFAULT 'BDT',
            `date` DATE NOT NULL,
            `invoice_no` VARCHAR(255) NULL,
            `description` TEXT NULL,
            `status` VARCHAR(50) DEFAULT 'pending',
            `notes` TEXT NULL,
            `created_by` INT NULL,
            `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS `audit_logs` (
            `id` INTEGER PRIMARY KEY AUTOINCREMENT,
            `user_id` INT NULL,
            `action` VARCHAR(50) NOT NULL,
            `description` TEXT NULL,
            `entity_type` VARCHAR(50) NULL,
            `entity_id` INT NULL,
            `old_values` TEXT NULL,
            `new_values` TEXT NULL,
            `ip_address` VARCHAR(50) NULL,
            `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS `recycle_bin` (
            `id` INTEGER PRIMARY KEY AUTOINCREMENT,
            `entity_table` VARCHAR(120) NOT NULL,
            `entity_id` INT NULL,
            `payload` LONGTEXT NOT NULL,
            `reason` VARCHAR(300) NULL,
            `deleted_by` INT NULL,
            `deleted_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            `restored_by` INT NULL,
            `restored_at` TIMESTAMP NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS `documents` (
            `id` INTEGER PRIMARY KEY AUTOINCREMENT,
            `name` VARCHAR(255) NOT NULL,
            `file_path` VARCHAR(500) NOT NULL,
            `file_type` VARCHAR(50) NULL,
            `entity_type` VARCHAR(50) NULL,
            `entity_id` INT NULL,
            `uploaded_by` INT NULL,
            `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS `currencies` (
            `id` INTEGER PRIMARY KEY AUTOINCREMENT,
            `code` VARCHAR(10) NOT NULL UNIQUE,
            `name` VARCHAR(100) NULL,
            `symbol` VARCHAR(10) NULL,
            `exchange_rate_to_base` DECIMAL(15,6) DEFAULT 1.0,
            `is_base` TINYINT(1) DEFAULT 0,
            `is_active` TINYINT(1) DEFAULT 1,
            `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS `settings` (
            `id` INTEGER PRIMARY KEY AUTOINCREMENT,
            `key` VARCHAR(100) NOT NULL UNIQUE,
            `value` TEXT NULL,
            `category` VARCHAR(50) DEFAULT 'general',
            `description` VARCHAR(300) NULL,
            `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def _run_migrations(cursor) -> None:
    for name, definition in [
        ("email", "VARCHAR(255) NULL"),
        ("password", "VARCHAR(255) NULL"),
        ("first_name", "VARCHAR(255) NULL"),
        ("last_name", "VARCHAR(255) NULL"),
        ("role", "VARCHAR(50) NULL"),
        ("is_active", "TINYINT(1) DEFAULT 1"),
    ]:
        _ensure_column(cursor, "users", name, definition)

    for name, definition in [
        ("name", "VARCHAR(255) NULL"),
        ("icon", "VARCHAR(50) NULL"),
        ("description", "TEXT NULL"),
        ("is_default", "TINYINT(1) DEFAULT 1"),
        ("parent_id", "INT NULL"),
        ("sort_order", "INT DEFAULT 0"),
    ]:
        _ensure_column(cursor, "cost_categories", name, definition)

    for name, definition in [
        ("name", "VARCHAR(255) NULL"),
        ("description", "TEXT NULL"),
        ("color", "VARCHAR(50) DEFAULT '#3b82f6'"),
    ]:
        _ensure_column(cursor, "investor_types", name, definition)

    for name, definition in [
        ("name", "VARCHAR(255) NULL"),
        ("subject", "VARCHAR(255) NULL"),
        ("body", "TEXT NULL"),
        ("is_system", "TINYINT(1) DEFAULT 0"),
    ]:
        _ensure_column(cursor, "email_templates", name, definition)

    for name, definition in [
        ("code", "VARCHAR(10) NULL"),
        ("name", "VARCHAR(80) NULL"),
        ("symbol", "VARCHAR(10) NULL"),
        ("exchange_rate_to_base", "DECIMAL(15,6) DEFAULT 1.0"),
        ("is_base", "TINYINT(1) DEFAULT 0"),
        ("is_active", "TINYINT(1) DEFAULT 1"),
    ]:
        _ensure_column(cursor, "currencies", name, definition)

    for name, definition in [
        ("key", "VARCHAR(100) NULL"),
        ("value", "TEXT NULL"),
        ("category", "VARCHAR(50) DEFAULT 'general'"),
        ("description", "VARCHAR(300) NULL"),
    ]:
        _ensure_column(cursor, "settings", name, definition)

    # Ensure extra columns exist on cost_items (migration for existing DBs)
    for i in range(1, 11):
        _ensure_column(cursor, "cost_items", f"extra_{i}", "TEXT NULL")


def init_sqlite_db(conn) -> None:
    """Create/upgrade schema and seed baseline rows if missing."""
    cursor = conn.cursor()
    _create_tables(cursor)
    _run_migrations(cursor)

    cursor.execute("SELECT `id`, `password` FROM `users` WHERE `username`=? LIMIT 1", ("admin",))
    admin_row = cursor.fetchone()
    if not admin_row:
        cursor.execute(
            "INSERT INTO `users` (`username`, `email`, `password`, `first_name`, `last_name`, `role`, `is_active`) "
            "VALUES (?, ?, ?, ?, ?, ?, 1)",
            ("admin", "admin@local", DEFAULT_ADMIN_HASH, "System", "Admin", "superadmin"),
        )
    else:
        current_hash = admin_row["password"]
        if current_hash == LEGACY_ADMIN_HASH:
            cursor.execute("UPDATE `users` SET `password`=? WHERE `username`=?", (DEFAULT_ADMIN_HASH, "admin"))

    cursor.execute("SELECT COUNT(*) AS cnt FROM `cost_categories`")
    if (_first_value(cursor.fetchone()) or 0) == 0:
        for idx, (name, icon, desc) in enumerate(COST_CATEGORIES):
            cursor.execute(
                "INSERT INTO `cost_categories` (`name`, `icon`, `description`, `sort_order`) VALUES (?, ?, ?, ?)",
                (name, icon, desc, idx * 10),
            )

    cursor.execute("SELECT COUNT(*) AS cnt FROM `investor_types`")
    if (_first_value(cursor.fetchone()) or 0) == 0:
        for name, desc, color in INVESTOR_TYPES:
            cursor.execute(
                "INSERT INTO `investor_types` (`name`, `description`, `color`) VALUES (?, ?, ?)",
                (name, desc, color),
            )

    cursor.execute("SELECT COUNT(*) AS cnt FROM `email_templates`")
    if (_first_value(cursor.fetchone()) or 0) == 0:
        templates = [
            (
                "Welcome to CMS",
                "Welcome to our Project '{project}'",
                "Dear {name},\n\nWelcome aboard! We are thrilled to have you as a valued {type} in our project '{project}'.\n\nYour portal access will be granted shortly.\n\nBest Regards,\nThe Management Team",
                1,
            ),
            (
                "Investment Received",
                "Receipt for Payment: ৳{amount}",
                "Dear {name},\n\nThis is to confirm that we have successfully received your payment of ৳{amount} on {date} for the project '{project}'.\n\nThank you for your continued trust and investment.\n\nBest Regards,\nFinance Department",
                1,
            ),
            (
                "Payment Overdue Reminder",
                "ACTION REQUIRED: Overdue Payment for '{project}'",
                "Dear {name},\n\nThis is a gentle reminder that your scheduled payment of ৳{amount} for the project '{project}' was due on {date} and is currently marked as overdue.\n\nPlease arrange for payment as soon as possible to avoid any project delays.\n\nBest Regards,\nFinance Department",
                1,
            ),
        ]
        for name, subj, body, is_system in templates:
            cursor.execute(
                "INSERT INTO `email_templates` (`name`, `subject`, `body`, `is_system`) VALUES (?, ?, ?, ?)",
                (name, subj, body, is_system),
            )

    settings_columns = _table_columns(cursor, "settings")
    key_col = "key" if "key" in settings_columns else ("setting_key" if "setting_key" in settings_columns else None)
    value_col = "value" if "value" in settings_columns else ("setting_value" if "setting_value" in settings_columns else None)

    if key_col and value_col:
        cursor.execute("SELECT COUNT(*) AS cnt FROM `settings`")
        if (_first_value(cursor.fetchone()) or 0) == 0:
            defaults = [
                ("currency_base", "BDT", "financial"),
                ("currency_symbol", "৳", "financial"),
                ("tax_rate", "15", "financial"),
            ]
            for key, value, category in defaults:
                cursor.execute(
                    f"INSERT INTO `settings` (`{key_col}`, `{value_col}`, `category`) VALUES (?, ?, ?)",
                    (key, value, category),
                )

    cursor.execute("SELECT COUNT(*) AS cnt FROM `currencies`")
    if (_first_value(cursor.fetchone()) or 0) == 0:
        currencies = [
            ("BDT", "Bangladeshi Taka", "৳", 1.0, 1, 1),
            ("USD", "US Dollar", "$", 0.0085, 0, 1),
            ("EUR", "Euro", "€", 0.0078, 0, 1),
            ("GBP", "British Pound", "£", 0.0067, 0, 1),
        ]
        for code, name, symbol, rate, is_base, is_active in currencies:
            cursor.execute(
                "INSERT INTO `currencies` (`code`, `name`, `symbol`, `exchange_rate_to_base`, `is_base`, `is_active`) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (code, name, symbol, rate, is_base, is_active),
            )

    conn.commit()


def clear_sqlite_db(conn, *, keep_tables: Iterable[str] | None = None) -> None:
    keep = set(keep_tables or [])
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    rows = cursor.fetchall()
    tables = [row["name"] for row in rows if row["name"] not in keep]
    
    for table in tables:
        cursor.execute(f"DELETE FROM `{table}`")
        cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")

    init_sqlite_db(conn)
