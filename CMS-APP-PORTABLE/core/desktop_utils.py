from datetime import date, datetime

from core.database import DB_TYPE, get_existing_column


IS_SQLITE = DB_TYPE == "sqlite"


def sql_now():
    return "CURRENT_TIMESTAMP" if IS_SQLITE else "NOW()"


def sql_today():
    return "DATE('now')" if IS_SQLITE else "CURDATE()"


def pick_column(table_name, *candidates, fallback=None):
    column = get_existing_column(table_name, *candidates)
    if column:
        return column
    return fallback or (candidates[0] if candidates else None)


def pick_value(row, *keys, default=None):
    for key in keys:
        if key in row and row[key] is not None:
            return row[key]
    return default


def as_float(value, default=0.0):
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_date(value):
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    if isinstance(value, str):
        trimmed = value.strip()
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d %b %Y", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(trimmed, fmt)
            except ValueError:
                continue
    return None


def format_date(value, fmt="%Y-%m-%d", default="—"):
    parsed = parse_date(value)
    return parsed.strftime(fmt) if parsed else default


def is_past_date(value):
    parsed = parse_date(value)
    if not parsed:
        return False
    return parsed.date() < datetime.now().date()


def bool_text(value, true_text="Active", false_text="Inactive"):
    return true_text if bool(value) else false_text
