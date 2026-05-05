"""
Shared constants + helpers for the Projects UI.
Keeps formatting and option lists consistent across view/layout modules.
"""

from __future__ import annotations

from datetime import datetime


STATUS_COLORS = {
    "planning": "#4f8cff",
    "active": "#27d3a2",
    "paused": "#f6c85f",
    "completed": "#9b8cff",
    "cancelled": "#ff7a90",
}

TYPE_OPTIONS = ["residential", "commercial", "mixed", "industrial", "land_development", "renovation"]
LISTING_OPTIONS = ["Sale", "Rent", "Lease", "Joint Venture", "Other"]
TRANSACTION_OPTIONS = ["New", "Resale", "Developer Sale", "Joint Venture", "Lease Transfer", "Assignment"]
CONSTRUCTION_OPTIONS = ["Under Construction", "Ready to Move", "Almost Ready", "Newly Launched", "Upcoming", "Handed Over"]
BEDROOM_OPTIONS = ["Studio", "1", "2", "3", "4", "5", "6+"]
BATHROOM_OPTIONS = ["1", "2", "3", "4", "5", "6+"]
BALCONY_OPTIONS = ["0", "1", "2", "3", "4", "5+"]
GARAGE_OPTIONS = ["No Parking", "1 Car", "2 Cars", "3 Cars", "4+ Cars"]
FLOOR_RANGE_OPTIONS = [str(i) for i in range(0, 41)] + ["41+"]
TOTAL_UNIT_OPTIONS = [str(i) for i in range(1, 121)] + ["120+"]

DETAIL_FIELDS = [
    ("Property Type", "property_type"),
    ("Property For", "property_for"),
    ("Location", "location"),
    ("Construction Status", "construction_status"),
    ("Property Size", "unit_size"),
    ("Transaction Type", "transaction_type"),
    ("Floor Available On", "floor_available_on"),
    ("Bedroom", "bedrooms"),
    ("Baths", "bathrooms"),
    ("Balconies", "balconies"),
    ("Garages", "garages"),
    ("Total Floor", "total_floors"),
    ("Furnishing", "furnishing"),
    ("Facing", "facing"),
    ("Land Area", "land_area"),
    ("Building Area", "building_area"),
    ("Start Date", "start_date"),
    ("Expected Completion", "estimated_end_date"),
]


def safe_float(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def safe_int(value):
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0


def humanize(value):
    text = str(value or "").replace("_", " ").strip()
    return text.title() if text else ""


def display(value, fallback="Not added yet"):
    text = str(value or "").strip()
    return text if text else fallback


def format_currency(value):
    return f"BDT {safe_float(value):,.0f}"


def format_date(value):
    if not value:
        return "TBD"
    if isinstance(value, datetime):
        return value.strftime("%d %b %Y")
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).strftime("%d %b %Y")
        except ValueError:
            continue
    return text or "TBD"


def split_items(value):
    items = []
    for line in str(value or "").replace("\r", "\n").split("\n"):
        for part in line.split(","):
            cleaned = part.strip().lstrip("-").lstrip("*").strip()
            if cleaned:
                items.append(cleaned)
    return items


def validate_date(value, label):
    text = str(value or "").strip()
    if not text:
        return None
    try:
        datetime.strptime(text, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"{label} must use YYYY-MM-DD.") from exc
    return text
