"""
Helpers for transaction display and lightweight editing.
"""

from core.desktop_utils import as_float, format_date


ENTRY_PREFIXES = {
    "investment": "I",
    "sale": "S",
    "buy": "B",
    "cost": "C",
    "expense": "E",
    "refund_in": "RI",
    "refund_out": "RO",
    "other_inflow": "OI",
    "other_outflow": "OO",
    "schedule_payment": "SC",
    "contractor_payment": "CP",
}


EDITABLE_META = {
    "investments": {"reference": "reference_no", "notes": "notes"},
    "cash_transactions": {"reference": "reference_no", "notes": "notes"},
    "cost_items": {"reference": "invoice_no", "notes": "notes"},
    "contractor_payments": {"reference": "invoice_no", "notes": "notes"},
    "payment_schedules": {"reference": None, "notes": "notes"},
}


def transaction_prefix(row):
    entry_type = str(row.get("entry_type") or "").strip().lower()
    source_table = str(row.get("source_table") or "").strip().lower()

    if entry_type in ENTRY_PREFIXES:
        return ENTRY_PREFIXES[entry_type]
    if source_table in ENTRY_PREFIXES:
        return ENTRY_PREFIXES[source_table]
    if source_table == "payment_schedules":
        return "SC"
    if source_table == "cost_items":
        return "C"
    if source_table == "contractor_payments":
        return "CP"
    return "GEN"


def transaction_code(row):
    prefix = transaction_prefix(row)
    try:
        source_id = int(float(row.get("source_id") or 0))
    except (TypeError, ValueError):
        source_id = 0
    if source_id > 0:
        return f"TRX-{prefix}-{source_id:06d}"
    return f"TRX-{prefix}-NEW"


def transaction_source_label(row):
    value = row.get("source_name") or row.get("source_table") or ""
    return str(value).replace("_", " ").title() or "Manual"


def transaction_party_label(row):
    return row.get("party_name") or row.get("counterparty") or "N/A"


def transaction_detail_rows(row):
    direction = "Money In" if row.get("direction") == "inflow" else "Money Out"
    amount = f"BDT {as_float(row.get('amount')):,.0f}"

    details = [
        ("Transaction ID", transaction_code(row)),
        ("Type", row.get("kind") or "Transaction"),
        ("Direction", direction),
        ("Amount", amount),
        ("Date", format_date(row.get("tx_date"))),
        ("Project", row.get("project_name") or "Unassigned"),
        ("Party", transaction_party_label(row)),
        ("Payment Method", str(row.get("payment_method") or "N/A").replace("_", " ").title()),
        ("Source", transaction_source_label(row)),
    ]
    return details


def editable_meta_for_row(row):
    return EDITABLE_META.get(str(row.get("source_table") or "").strip().lower())
