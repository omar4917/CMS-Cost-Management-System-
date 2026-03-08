"""
AI Service for CMS Desktop App.
Connects to Groq API (OpenAI-compatible) to provide intelligent assistance
for cost estimation, project analysis, investor insights, and more.
Supports switching between Groq, OpenAI, and Gemini APIs.
"""

import os
import sys

import requests
from dotenv import load_dotenv, set_key

from core.database import execute_query


if getattr(sys, "frozen", False):
    app_dir = os.path.dirname(sys.executable)
else:
    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ENV_PATH = os.path.join(app_dir, ".env")
load_dotenv(ENV_PATH)


PROVIDERS = {
    "groq": {
        "name": "Groq (Llama 3)",
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "model": "llama-3.3-70b-versatile",
        "key_prefix": "gsk_",
    },
    "openai": {
        "name": "OpenAI (GPT-4)",
        "url": "https://api.openai.com/v1/chat/completions",
        "model": "gpt-4o-mini",
        "key_prefix": "sk-",
    },
    "gemini": {
        "name": "Google Gemini",
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "model": "gemini-2.0-flash",
        "key_prefix": "AI",
    },
}


def _normalize_provider(provider):
    provider_key = str(provider or "").strip().lower()
    return provider_key if provider_key in PROVIDERS else "groq"


_config = {
    "provider": _normalize_provider(os.getenv("AI_PROVIDER", "groq")),
    "api_key": os.getenv("AI_API_KEY", "").strip(),
}


def set_provider(provider, api_key):
    """Switch AI provider."""
    _config["provider"] = _normalize_provider(provider)
    _config["api_key"] = (api_key or "").strip()
    os.environ["AI_PROVIDER"] = _config["provider"]
    os.environ["AI_API_KEY"] = _config["api_key"]


def save_provider_settings(provider, api_key):
    """Persist AI provider settings in the local env file."""
    set_provider(provider, api_key)
    if not os.path.exists(ENV_PATH):
        with open(ENV_PATH, "a", encoding="utf-8"):
            pass
    set_key(ENV_PATH, "AI_PROVIDER", _config["provider"])
    set_key(ENV_PATH, "AI_API_KEY", _config["api_key"])


def get_provider():
    return _config["provider"], PROVIDERS.get(_config["provider"], PROVIDERS["groq"])


def get_system_context():
    """Build a system prompt with live CMS data context."""
    context_parts = [
        "You are CMS AI - an intelligent assistant for a Real Estate Cost Management System. "
        "You help admins with cost estimation, project analysis, investor insights, financial calculations, "
        "budget comparisons, and general advice about real estate development.\n"
        "You have access to the following live database summary:\n"
    ]

    try:
        projects = execute_query(
            "SELECT name, status, total_budget, progress, location FROM projects ORDER BY created_at DESC LIMIT 10"
        )
        if projects:
            context_parts.append("PROJECTS:")
            for project in projects:
                budget = float(project.get("total_budget", 0) or 0)
                context_parts.append(
                    f"  - {project['name']} | {project['status']} | Budget: BDT {budget:,.0f} | "
                    f"Progress: {project.get('progress', 0)}% | {project.get('location', 'N/A')}"
                )

        inv_total = execute_query("SELECT COALESCE(SUM(amount), 0) AS total FROM investments WHERE status='confirmed'")
        cost_total = execute_query("SELECT COALESCE(SUM(actual_amount), 0) AS total FROM cost_items")
        budget_total = execute_query("SELECT COALESCE(SUM(total_budget), 0) AS total FROM projects")
        overdue = execute_query(
            "SELECT COUNT(*) AS cnt FROM payment_schedules "
            "WHERE status='overdue' OR (status='pending' AND due_date < CURDATE())"
        )
        inv_count = execute_query("SELECT COUNT(*) AS cnt FROM investors WHERE is_active=1")

        context_parts.append("\nFINANCIAL SUMMARY:")
        context_parts.append(f"  Total Budget: BDT {float(budget_total[0]['total'] or 0):,.0f}")
        context_parts.append(f"  Total Invested: BDT {float(inv_total[0]['total'] or 0):,.0f}")
        context_parts.append(f"  Total Costs (Actual): BDT {float(cost_total[0]['total'] or 0):,.0f}")
        context_parts.append(f"  Overdue Payments: {overdue[0]['cnt']}")
        context_parts.append(f"  Active Investors: {inv_count[0]['cnt']}")

        top_cats = execute_query(
            "SELECT cc.name, COALESCE(SUM(ci.actual_amount), 0) AS total "
            "FROM cost_items ci "
            "JOIN cost_categories cc ON ci.category_id = cc.id "
            "GROUP BY cc.name ORDER BY total DESC LIMIT 5"
        )
        if top_cats:
            context_parts.append("\nTOP COST CATEGORIES:")
            for category in top_cats:
                context_parts.append(f"  - {category['name']}: BDT {float(category['total']):,.0f}")

    except Exception as exc:
        context_parts.append(f"(Database context unavailable: {exc})")

    context_parts.append(
        "\nCurrency: BDT (Bangladeshi Taka). Always be helpful, precise with numbers, and provide actionable insights."
    )
    context_parts.append("\n[ACTION EXECUTION AUTHORITY]")
    context_parts.append("The user has granted you full authority to act on their behalf.")
    context_parts.append(
        "If the user asks you to add, create, update, or delete data, you MUST do it by outputting JSON action blocks."
    )
    context_parts.append(
        "CRITICAL: Output exactly one valid JSON object per line inside a ```json code block (JSONL format). "
        "Do not pretty-print JSON across multiple lines."
    )
    context_parts.append(
        "If the user asks for dummy, sample, fake, or demo data, create complete linked records with realistic values "
        "instead of sparse placeholder rows."
    )
    context_parts.append("Each line must be a complete, self-contained JSON object like:")
    context_parts.append("```json")
    context_parts.append(
        '{"execute_action": "insert", "table": "investors", "data": {"name": "Jane Doe", "email": "jane@test.com", "phone": "01712345671", "company": "ABC Corp", "is_active": 1}}'
    )
    context_parts.append(
        '{"execute_action": "insert", "table": "investors", "data": {"name": "Bob Smith", "email": "bob@test.com", "phone": "01712345672", "company": "XYZ Ltd", "is_active": 1}}'
    )
    context_parts.append("```")
    context_parts.append("Valid execute_action values: 'insert', 'update', 'delete'.")
    context_parts.append("For 'update' and 'delete', include the 'id' inside the 'data' object.")
    context_parts.append("Do not include 'id' for 'insert' because it is auto-increment.")
    context_parts.append("Use lowercase enum values exactly as listed.")
    context_parts.append("\n[DATABASE TABLE SCHEMAS - use EXACTLY these column names]")
    context_parts.append(
        "projects: name, description, location, type('residential'|'commercial'|'mixed'|'industrial'|'land_development'|'renovation'), "
        "status('planning'|'active'|'paused'|'completed'|'cancelled'), start_date(YYYY-MM-DD), estimated_end_date, actual_end_date, "
        "total_budget(DECIMAL), progress(INT 0-100), total_floors(INT), total_units(INT), land_area, building_area, created_by(INT)"
    )
    context_parts.append(
        "investors: name, email, phone, address, type_id(INT FK investor_types), company, national_id, bank_name, bank_account, is_active(BOOL 1/0), notes"
    )
    context_parts.append("investor_types: name, description, color")
    context_parts.append(
        "investments: investor_id(INT FK), project_id(INT FK), amount(DECIMAL), currency('BDT'), date(YYYY-MM-DD), "
        "payment_method('cash'|'bank_transfer'|'cheque'|'online'|'other'), reference_no, status('pending'|'confirmed'|'cancelled'), notes, created_by(INT)"
    )
    context_parts.append(
        "payment_schedules: investor_id(INT FK), project_id(INT FK), installment_no(INT), amount(DECIMAL), due_date(YYYY-MM-DD), "
        "paid_date, paid_amount(DECIMAL), status('pending'|'paid'|'overdue'|'partial'), reminder_sent(BOOL), notes"
    )
    context_parts.append("cost_categories: name, icon, description, is_default(BOOL), parent_id(INT nullable)")
    context_parts.append(
        "cost_items: name, project_id(INT FK), category_id(INT FK), description, quantity(DECIMAL), unit, unit_price(DECIMAL), "
        "estimated_amount(DECIMAL), actual_amount(DECIMAL), currency('BDT'), date(YYYY-MM-DD), vendor, invoice_no, "
        "status('pending'|'approved'|'purchased'|'delivered'|'paid'|'rejected'|'cancelled'), notes, created_by(INT)"
    )
    context_parts.append(
        "cash_transactions: project_id(INT nullable), investor_id(INT nullable), contractor_id(INT nullable), "
        "entry_type('investment'|'sale'|'buy'|'cost'|'expense'|'refund_in'|'refund_out'|'other_inflow'|'other_outflow'), "
        "direction('inflow'|'outflow'), amount(DECIMAL), currency('BDT'), tx_date(YYYY-MM-DD), counterparty, reference_no, "
        "payment_method, status('confirmed'|'pending'|'cancelled'), source_table, source_id(INT nullable), notes, created_by(INT)"
    )
    context_parts.append("contractors: name, email, phone, company, specialization, is_active(BOOL 1/0)")
    context_parts.append(
        "contractor_payments: contractor_id(INT FK), project_id(INT FK), amount(DECIMAL), currency('BDT'), date(YYYY-MM-DD), "
        "invoice_no, description, status('pending'|'approved'|'paid'), notes, created_by(INT)"
    )
    context_parts.append(
        "Use cash_transactions for manual buy/sell/cost/expense/refund flows that are not formal investment rows."
    )
    context_parts.append("IMPORTANT: created_at and updated_at are auto-managed. Do not include them in action payloads.")

    return "\n".join(context_parts)


def chat(messages, temperature=0.7):
    """Send messages to the AI provider and get a response."""
    _, provider = get_provider()
    api_key = _config["api_key"]

    if not api_key:
        return "No API key configured. Go to AI Settings to add your API key."

    full_messages = [{"role": "system", "content": get_system_context()}] + messages
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": provider["model"],
        "messages": full_messages,
        "temperature": temperature,
        "max_tokens": 2048,
    }

    try:
        response = requests.post(provider["url"], headers=headers, json=payload, timeout=(8, 45))
        if response.status_code != 200:
            error_msg = response.json().get("error", {}).get("message", response.text[:200])
            return f"API Error ({response.status_code}): {error_msg}"

        data = response.json()
        return data["choices"][0]["message"]["content"]
    except requests.exceptions.Timeout:
        return "Request timed out. The AI server may be busy. Try again."
    except requests.exceptions.ConnectionError:
        return "Cannot connect to the AI server. Check your internet connection."
    except Exception as exc:
        return f"Error: {exc}"


def analyze_project(project_name):
    """Quick project analysis."""
    return chat(
        [
            {
                "role": "user",
                "content": (
                    f"Analyze the project '{project_name}' from our database. "
                    "Provide a summary of budget utilization, progress status, and any concerns or recommendations."
                ),
            }
        ]
    )


def estimate_cost(description):
    """Get AI cost estimation for a material or service."""
    return chat(
        [
            {
                "role": "user",
                "content": (
                    "As a real estate construction expert in Bangladesh, estimate the cost for: "
                    f"{description}. Provide a price range in BDT, the factors that affect pricing, "
                    "and tips for getting the best price."
                ),
            }
        ]
    )


def suggest_budget_allocation(total_budget):
    """Get AI-suggested budget allocation for a new project."""
    return chat(
        [
            {
                "role": "user",
                "content": (
                    f"For a new real estate development project with a total budget of BDT {total_budget:,.0f} "
                    "in Bangladesh, suggest a detailed budget allocation breakdown by category "
                    "(land, construction, legal, marketing, etc.) with percentages and amounts."
                ),
            }
        ]
    )
