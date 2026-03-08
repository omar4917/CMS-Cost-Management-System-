import json
import re
from datetime import date

from core.database import ensure_cash_transactions_table, execute_query, get_table_columns
from core.demo_data import seed_connected_demo_data


GLOBAL_ALIASES = {
    "typeId": "type_id",
    "bankName": "bank_name",
    "bankAccount": "bank_account",
    "nationalId": "national_id",
    "isActive": "is_active",
    "projectId": "project_id",
    "categoryId": "category_id",
    "investorId": "investor_id",
    "contractorId": "contractor_id",
    "paymentMethod": "payment_method",
    "referenceNo": "reference_no",
    "paidDate": "paid_date",
    "paidAmount": "paid_amount",
    "dueDate": "due_date",
    "reminderSent": "reminder_sent",
    "invoiceNo": "invoice_no",
    "createdBy": "created_by",
    "approvedBy": "approved_by",
    "firstName": "first_name",
    "lastName": "last_name",
    "transactionDate": "tx_date",
    "transactionType": "entry_type",
    "counterParty": "counterparty",
}

TABLE_NAME_ALIASES = {
    "transaction": "cash_transactions",
    "transactions": "cash_transactions",
    "financial_transactions": "cash_transactions",
    "ledger_transactions": "cash_transactions",
    "cash_flow": "cash_transactions",
}

TABLE_ALIASES = {
    "projects": {
        "budget": "total_budget",
        "estimated_cost": "total_budget",
        "end_date": "estimated_end_date",
        "est_end_date": "estimated_end_date",
    },
    "contractor_payments": {
        "payment_date": "date",
    },
    "cash_transactions": {
        "type": "entry_type",
        "transaction_type": "entry_type",
        "transaction_date": "tx_date",
        "date": "tx_date",
        "vendor": "counterparty",
        "seller": "counterparty",
        "buyer": "counterparty",
        "customer": "counterparty",
        "party": "counterparty",
        "source": "source_table",
    },
}

TABLE_DEFAULTS = {
    "projects": lambda user_id: {
        "type": "residential",
        "status": "planning",
        "progress": 0,
        "total_budget": 0,
        "created_by": user_id,
    },
    "investors": lambda _user_id: {
        "is_active": 1,
    },
    "investments": lambda user_id: {
        "currency": "BDT",
        "date": date.today().isoformat(),
        "payment_method": "bank_transfer",
        "status": "confirmed",
        "created_by": user_id,
    },
    "payment_schedules": lambda _user_id: {
        "status": "pending",
        "reminder_sent": 0,
        "paid_amount": 0,
    },
    "cost_categories": lambda _user_id: {
        "is_default": 0,
    },
    "cost_items": lambda user_id: {
        "currency": "BDT",
        "status": "pending",
        "quantity": 0,
        "unit": "pcs",
        "estimated_amount": 0,
        "actual_amount": 0,
        "created_by": user_id,
    },
    "contractors": lambda _user_id: {
        "is_active": 1,
    },
    "contractor_payments": lambda user_id: {
        "currency": "BDT",
        "date": date.today().isoformat(),
        "status": "paid",
        "created_by": user_id,
    },
    "cash_transactions": lambda user_id: {
        "currency": "BDT",
        "tx_date": date.today().isoformat(),
        "status": "confirmed",
        "source_table": "manual",
        "created_by": user_id,
    },
}


def extract_actions(text):
    actions = []
    seen = set()

    blocks = re.findall(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    for block in blocks:
        for item in _extract_json_candidates(block):
            key = json.dumps(item, sort_keys=True)
            if key not in seen:
                seen.add(key)
                actions.append(item)

    if not actions:
        for item in _extract_json_candidates(text):
            key = json.dumps(item, sort_keys=True)
            if key not in seen:
                seen.add(key)
                actions.append(item)

    return actions


def _extract_json_candidates(source):
    candidates = []
    for line in source.splitlines():
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and {"execute_action", "table", "data"} <= set(obj):
            candidates.append(obj)

    if candidates:
        return candidates

    try:
        obj = json.loads(source)
    except json.JSONDecodeError:
        return []

    if isinstance(obj, dict) and {"execute_action", "table", "data"} <= set(obj):
        return [obj]
    if isinstance(obj, list):
        return [item for item in obj if isinstance(item, dict) and {"execute_action", "table", "data"} <= set(item)]
    return []


def execute_actions(actions, user_id=None):
    executed = 0
    for raw_action in actions:
        normalized = normalize_action(raw_action, user_id=user_id)
        if not normalized:
            continue

        action = normalized["execute_action"]
        table = normalized["table"]
        payload = normalized["data"]

        if action == "insert":
            cols = list(payload.keys())
            if not cols:
                continue
            query = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join(['%s'] * len(cols))})"
            execute_query(query, tuple(payload[col] for col in cols), fetch=False)
            executed += 1
        elif action == "update":
            record_id = payload.pop("id", None)
            if not record_id or not payload:
                continue
            cols = list(payload.keys())
            sets = ", ".join(f"{col}=%s" for col in cols)
            query = f"UPDATE {table} SET {sets} WHERE id=%s"
            execute_query(query, tuple(payload[col] for col in cols) + (record_id,), fetch=False)
            executed += 1
        elif action == "delete":
            record_id = payload.get("id")
            if not record_id:
                continue
            execute_query(f"DELETE FROM {table} WHERE id=%s", (record_id,), fetch=False)
            executed += 1

    return executed


def normalize_action(action, user_id=None):
    table = str(action.get("table", "")).strip().lower()
    table = TABLE_NAME_ALIASES.get(table, table)
    verb = str(action.get("execute_action", "")).strip().lower()
    payload = action.get("data") or {}

    if not table or not verb or not isinstance(payload, dict):
        return None

    if table == "cash_transactions":
        ensure_cash_transactions_table()

    columns = get_table_columns(table)
    if not columns:
        return None

    normalized = {}
    table_aliases = TABLE_ALIASES.get(table, {})

    for key, value in payload.items():
        mapped_key = table_aliases.get(key, GLOBAL_ALIASES.get(key, key))
        if mapped_key not in columns:
            continue
        normalized[mapped_key] = _normalize_value(table, mapped_key, value)

    defaults = TABLE_DEFAULTS.get(table)
    if callable(defaults):
        for key, value in defaults(user_id).items():
            if key in columns and key not in normalized and value is not None:
                normalized[key] = value

    if verb == "insert":
        normalized.pop("id", None)
        if table == "cost_items" and "name" not in normalized and payload.get("description"):
            normalized["name"] = str(payload["description"])[:300]
        if table == "projects" and "name" not in normalized and payload.get("title"):
            normalized["name"] = str(payload["title"])[:200]
        if "created_by" in columns and user_id and "created_by" not in normalized:
            normalized["created_by"] = user_id
    else:
        record_id = payload.get("id")
        if record_id is None:
            return None
        normalized["id"] = record_id

    if table == "contractor_payments" and "date" not in normalized and "payment_date" in payload:
        normalized["date"] = payload["payment_date"]

    if table == "cash_transactions":
        if "entry_type" not in normalized and payload.get("type"):
            normalized["entry_type"] = _normalize_value(table, "entry_type", payload.get("type"))
        if "direction" not in normalized:
            normalized["direction"] = _default_cash_direction(normalized.get("entry_type"), payload)
        if "tx_date" not in normalized and payload.get("date"):
            normalized["tx_date"] = payload["date"]
        if "counterparty" not in normalized:
            for alias in ("counterparty", "vendor", "buyer", "seller", "customer", "name"):
                if payload.get(alias):
                    normalized["counterparty"] = str(payload[alias])[:255]
                    break

    return {
        "execute_action": verb,
        "table": table,
        "data": normalized,
    }


def _normalize_value(table, key, value):
    if value is None:
        return None

    if table == "projects" and key == "type":
        return {
            "residential": "residential",
            "commercial": "commercial",
            "mixed": "mixed",
            "mixed_use": "mixed",
            "mixed use": "mixed",
            "industrial": "industrial",
            "land": "land_development",
            "land_development": "land_development",
            "renovation": "renovation",
        }.get(str(value).strip().lower(), "residential")

    if key == "status":
        mapped = {
            "in progress": "active",
            "ongoing": "active",
            "planned": "planning",
            "complete": "completed",
            "completed": "completed",
            "done": "completed",
            "hold": "paused",
            "stopped": "paused",
            "inactive": "paused",
            "completed_payment": "paid",
        }.get(str(value).strip().lower())
        if table == "contractor_payments":
            return {
                "completed": "paid",
                "approved": "approved",
                "paid": "paid",
                "pending": "pending",
            }.get(str(value).strip().lower(), "paid")
        if table == "payment_schedules":
            return {
                "partial": "partial",
                "paid": "paid",
                "pending": "pending",
                "overdue": "overdue",
                "cancelled": "pending",
            }.get(str(value).strip().lower(), "pending")
        if table == "cash_transactions":
            return {
                "paid": "confirmed",
                "approved": "confirmed",
                "confirmed": "confirmed",
                "pending": "pending",
                "cancelled": "cancelled",
                "rejected": "cancelled",
            }.get(str(value).strip().lower(), "confirmed")
        if mapped:
            return mapped

    if key in {"is_active", "reminder_sent"}:
        if isinstance(value, bool):
            return 1 if value else 0
        if isinstance(value, (int, float)):
            return 1 if value else 0
        return 1 if str(value).strip().lower() in {"true", "1", "yes", "active"} else 0

    if table == "cash_transactions" and key == "direction":
        return {
            "in": "inflow",
            "income": "inflow",
            "credit": "inflow",
            "receive": "inflow",
            "received": "inflow",
            "sale": "inflow",
            "sell": "inflow",
            "out": "outflow",
            "expense": "outflow",
            "debit": "outflow",
            "payment": "outflow",
            "buy": "outflow",
            "purchase": "outflow",
            "cost": "outflow",
        }.get(str(value).strip().lower(), str(value).strip().lower())

    if table == "cash_transactions" and key == "entry_type":
        return {
            "investment": "investment",
            "funding": "investment",
            "sell": "sale",
            "sale": "sale",
            "booking": "sale",
            "buy": "buy",
            "purchase": "buy",
            "cost": "cost",
            "expense": "expense",
            "refund in": "refund_in",
            "refund_in": "refund_in",
            "refund out": "refund_out",
            "refund_out": "refund_out",
            "income": "other_inflow",
            "other income": "other_inflow",
            "other inflow": "other_inflow",
            "other outflow": "other_outflow",
        }.get(str(value).strip().lower(), str(value).strip().lower())

    return value


def is_dummy_data_request(prompt):
    text = prompt.lower()
    return (
        "dummy" in text
        or "demo data" in text
        or "sample data" in text
        or "fake data" in text
        or ("seed" in text and "data" in text)
    )


def _default_cash_direction(entry_type, payload):
    entry = str(entry_type or payload.get("entry_type") or payload.get("type") or "").strip().lower()
    if entry in {"investment", "sale", "refund_in", "other_inflow", "collection"}:
        return "inflow"
    if entry in {"buy", "cost", "expense", "refund_out", "other_outflow"}:
        return "outflow"

    for key in ("direction", "flow"):
        if payload.get(key):
            return _normalize_value("cash_transactions", "direction", payload[key])

    return "outflow"


def handle_local_command(prompt, user_id=None):
    if is_dummy_data_request(prompt):
        count, summary = seed_connected_demo_data(user_id=user_id)
        return (
            "Created full demo records for the desktop app.\n\n"
            f"{summary}\n\n"
            f"*(Automatically executed {count} database actions)*"
        )
    return None


def seed_demo_data(user_id=None):
    return seed_connected_demo_data(user_id=user_id)
