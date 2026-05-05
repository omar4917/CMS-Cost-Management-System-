"""
Connected demo data seeding for the desktop app.
Creates realistic, linked records across the main desktop modules.
"""

import os
import sys
from datetime import date, timedelta

from core.database import ensure_cash_transactions_table, ensure_project_profile_columns, execute_query, get_table_columns
from core.schema_mysql import COST_CATEGORIES, INVESTOR_TYPES


EMAIL_TEMPLATES = [
    (
        "Project Launch Follow-up",
        "Welcome to {project}",
        "Dear {name},\n\nThank you for your interest in {project}. Our sales desk is ready to help with pricing, payment plan, and unit booking details.\n\nRegards,\nHouzez Sales",
        0,
    ),
    (
        "Installment Reminder",
        "Installment reminder for {project}",
        "Dear {name},\n\nThis is a reminder that your next installment for {project} is coming due soon. Please contact our finance desk if you need the latest statement.\n\nRegards,\nFinance Team",
        0,
    ),
    (
        "Payment Overdue Reminder",
        "ACTION REQUIRED: Overdue Payment for '{project}'",
        "Dear {name},\n\nThis is a gentle reminder that your scheduled payment of BDT {amount} for the project '{project}' was due on {date} and is currently marked as overdue.\n\nPlease arrange for payment as soon as possible to avoid any project delays.\n\nBest Regards,\nFinance Department",
        1,
    ),
]


def seed_connected_demo_data(user_id=None):
    ensure_project_profile_columns()
    ensure_cash_transactions_table()
    investor_types = _ensure_investor_types()
    cost_categories = _ensure_cost_categories()
    _ensure_email_templates()

    today = date.today()
    batch = int(execute_query("SELECT COALESCE(COUNT(*), 0) AS total FROM projects")[0]["total"] or 0) + 1
    batch_code = f"B{batch:02d}"

    projects = _insert_projects(today, batch_code, user_id)
    investors = _insert_investors(investor_types, batch_code)
    contractors = _insert_contractors(batch_code)
    investment_count = _insert_investments(today, batch_code, projects, investors, user_id)
    schedule_count = _insert_payment_schedules(today, batch_code, projects, investors)
    cost_count = _insert_cost_items(today, batch_code, projects, cost_categories, user_id)
    contractor_payment_count = _insert_contractor_payments(today, batch_code, projects, contractors, user_id)
    cash_count = _insert_cash_transactions(today, batch_code, projects, investors, contractors, user_id)
    try:
        email_log_count = _insert_email_logs(today, batch_code, projects, investors)
    except Exception:
        email_log_count = 0

    try:
        audit_count = _insert_audit_logs(batch_code, user_id, len(projects), len(investors), cost_count)
    except Exception:
        audit_count = 0

    total_records = (
        len(projects)
        + len(investors)
        + len(contractors)
        + investment_count
        + schedule_count
        + cost_count
        + contractor_payment_count
        + cash_count
        + email_log_count
        + audit_count
    )

    summary = (
        f"- Projects: {len(projects)}\n"
        f"- Investors: {len(investors)}\n"
        f"- Investor types linked: {len(investor_types)}\n"
        f"- Cost categories linked: {len(cost_categories)}\n"
        f"- Investments: {investment_count}\n"
        f"- Payment schedules: {schedule_count}\n"
        f"- Cost items: {cost_count}\n"
        f"- Contractors: {len(contractors)}\n"
        f"- Contractor payments: {contractor_payment_count}\n"
        f"- Cash transactions: {cash_count}\n"
        f"- Email logs: {email_log_count}\n"
        f"- Audit logs: {audit_count}"
    )
    return total_records, summary


def seed_connected_demo_data_if_empty(user_id=None):
    """Seed a connected desktop demo workspace only when the main tables are empty."""
    ensure_project_profile_columns()
    ensure_cash_transactions_table()
    _ensure_investor_types()
    _ensure_cost_categories()
    _ensure_email_templates()

    checkpoints = [
        "projects",
        "investors",
        "investments",
        "payment_schedules",
        "cost_items",
        "contractors",
    ]
    existing_rows = 0
    for table_name in checkpoints:
        existing_rows += int(execute_query(f"SELECT COALESCE(COUNT(*), 0) AS total FROM {table_name}")[0]["total"] or 0)

    if existing_rows:
        return 0, "Skipped automatic demo seed because the desktop workspace already contains data."

    return seed_connected_demo_data(user_id=user_id)


def _app_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _ensure_demo_project_covers(project_titles: list[str]) -> list[str | None]:
    """Create deterministic local cover images for demo projects.

    Returns DB-ready relative paths (forward slashes) under the app directory.
    """

    try:
        from PIL import Image, ImageDraw, ImageFont  # type: ignore
    except Exception:
        return [None for _ in project_titles]

    base_dir = _app_dir()
    out_dir = os.path.join(base_dir, "data", "demo_images")
    os.makedirs(out_dir, exist_ok=True)

    palette = [
        ((9, 28, 65), (79, 140, 255)),
        ((17, 24, 39), (16, 185, 129)),
        ((15, 23, 42), (245, 158, 11)),
        ((12, 18, 34), (236, 72, 153)),
        ((7, 17, 31), (99, 102, 241)),
        ((9, 14, 27), (34, 211, 238)),
    ]

    def _pick_fonts():
        try:
            return ImageFont.truetype("arial.ttf", 58), ImageFont.truetype("arial.ttf", 28)
        except Exception:
            default = ImageFont.load_default()
            return default, default

    font_title, font_sub = _pick_fonts()
    created_paths: list[str | None] = []

    width, height = 1400, 760
    for idx, title in enumerate(project_titles, start=1):
        filename = f"demo_project_cover_{idx:02d}.png"
        abs_path = os.path.join(out_dir, filename)
        rel_path = os.path.relpath(abs_path, base_dir).replace("\\", "/")

        if not os.path.exists(abs_path):
            start, end = palette[(idx - 1) % len(palette)]
            img = Image.new("RGBA", (width, height), (0, 0, 0, 255))
            draw = ImageDraw.Draw(img)

            for y in range(height):
                t = y / max(height - 1, 1)
                r = int(start[0] + (end[0] - start[0]) * t)
                g = int(start[1] + (end[1] - start[1]) * t)
                b = int(start[2] + (end[2] - start[2]) * t)
                draw.line([(0, y), (width, y)], fill=(r, g, b, 255))

            # Ambient geometry
            draw.ellipse([width - 430, -90, width + 120, 460], fill=(255, 255, 255, 18))
            draw.ellipse([width - 700, height - 480, width - 240, height - 20], fill=(0, 0, 0, 35))
            draw.rounded_rectangle([44, 44, 260, 120], radius=22, fill=(255, 255, 255, 20))
            draw.text((70, 70), "HOUZEZ DEMO", font=font_sub, fill=(255, 255, 255, 210))

            # Title block
            draw.rounded_rectangle([60, height - 220, width - 60, height - 60], radius=28, fill=(0, 0, 0, 90))
            draw.text((96, height - 198), title, font=font_title, fill=(248, 250, 252, 245))
            draw.text(
                (96, height - 118),
                "Sample cover image generated locally for the desktop demo workspace.",
                font=font_sub,
                fill=(203, 213, 225, 220),
            )

            try:
                img.save(abs_path, format="PNG", optimize=True)
            except Exception:
                try:
                    img.convert("RGB").save(abs_path, format="PNG")
                except Exception:
                    # If saving fails (permissions), just skip the cover.
                    created_paths.append(None)
                    continue

        created_paths.append(rel_path)

    return created_paths


def _ensure_investor_types():
    rows = execute_query("SELECT id, name FROM investor_types ORDER BY id ASC")
    if rows:
        return rows

    for name, description, color in INVESTOR_TYPES:
        execute_query(
            "INSERT INTO investor_types (name, description, color, created_at, updated_at) VALUES (%s, %s, %s, NOW(), NOW())",
            (name, description, color),
            fetch=False,
        )
    return execute_query("SELECT id, name FROM investor_types ORDER BY id ASC")


def _ensure_cost_categories():
    rows = execute_query("SELECT id, name FROM cost_categories ORDER BY sort_order ASC, id ASC")
    if rows:
        return rows

    for index, (name, icon, description) in enumerate(COST_CATEGORIES):
        execute_query(
            "INSERT INTO cost_categories (name, icon, description, is_default, sort_order, created_at, updated_at) "
            "VALUES (%s, %s, %s, 1, %s, NOW(), NOW())",
            (name, icon, description, index * 10),
            fetch=False,
        )
    return execute_query("SELECT id, name FROM cost_categories ORDER BY sort_order ASC, id ASC")


def _ensure_email_templates():
    try:
        existing_rows = execute_query("SELECT id, name FROM email_templates")
    except Exception:
        return

    columns = get_table_columns("email_templates")
    body_col = next((col for col in ("body", "body_html", "bodyHtml") if col in columns), None)
    if not body_col:
        return

    existing_names = {str(row.get("name") or "").strip() for row in existing_rows}
    for name, subject, body, is_system in EMAIL_TEMPLATES:
        if name in existing_names:
            continue
        payload = {
            "name": name,
            "subject": subject,
            body_col: body,
        }
        if "is_system" in columns:
            payload["is_system"] = is_system
        if "isSystem" in columns:
            payload["isSystem"] = is_system
        if "is_active" in columns:
            payload["is_active"] = 1
        if "isActive" in columns:
            payload["isActive"] = 1
        if "trigger_type" in columns:
            payload["trigger_type"] = "payment_overdue" if "Overdue" in name else "manual"
        if "triggerType" in columns:
            payload["triggerType"] = "payment_overdue" if "Overdue" in name else "manual"

        cols = list(payload.keys())
        execute_query(
            f"INSERT INTO email_templates ({', '.join(cols)}) VALUES ({', '.join(['%s'] * len(cols))})",
            tuple(payload[col] for col in cols),
            fetch=False,
        )


def _insert_projects(today, batch_code, user_id):
    project_specs = [
        {
            "name": f"Pinaki North Ridge Heights {batch_code}",
            "description": "A premium north-facing apartment tower in Uttara with two towers, wide frontage, rooftop amenities, and a sales-ready showroom experience inside the desktop app.",
            "location": "Uttara, Dhaka",
            "type": "residential",
            "property_type": "Apartment/Flats",
            "property_for": "Sale",
            "status": "active",
            "construction_status": "Almost Ready",
            "start_date": (today - timedelta(days=420)).isoformat(),
            "estimated_end_date": (today + timedelta(days=90)).isoformat(),
            "total_budget": 325000000,
            "progress": 84,
            "unit_size": "1100, 1126, 1145, 1216, 1230, 1270, 1300, 1311 sqft",
            "transaction_type": "New",
            "floor_available_on": "Any Floor",
            "bedrooms": "03",
            "bathrooms": "03",
            "balconies": "2",
            "garages": "No Parking",
            "total_floors": 11,
            "total_units": 96,
            "furnishing": "Unfurnished",
            "facing": "North Facing",
            "land_area": "25 katha",
            "building_area": "168000 sqft",
            "features": "Mosque/Prayer Room\nSecurity\nLift\nFire exit\nWASA connection\nSelf Water supply\nHot water\nCylinder Gas\nElectricity\nGenerator\nIntercom\nCCTV\nSatellite or cable TV\nGarden\nSolar panels\nFire Protection",
            "nearby_places": "Akij Foundation School and College\nSunbeam English Medium School\nMilestone School and College\nIUBAT University\nEast West Medical College\nAhsania Mission Cancer Hospital",
            "corporate_office": "Pinaki Holdings Limited, House 29, Garib-e-Newaz Avenue, Sector 11, Uttara, Dhaka 1230",
        },
        {
            "name": f"Freedom Lake Residences {batch_code}",
            "description": "A calm, design-forward apartment project built for family buyers who want landscaped open space, a clubhouse, and strong construction quality.",
            "location": "Bashundhara R/A, Dhaka",
            "type": "residential",
            "property_type": "Apartment/Flats",
            "property_for": "Sale",
            "status": "planning",
            "construction_status": "Launching Soon",
            "start_date": (today - timedelta(days=60)).isoformat(),
            "estimated_end_date": (today + timedelta(days=540)).isoformat(),
            "total_budget": 278000000,
            "progress": 12,
            "unit_size": "1700-2800 sqft single units, 3900 sqft duplex",
            "transaction_type": "New",
            "floor_available_on": "2nd-10th Floor",
            "bedrooms": "3-4",
            "bathrooms": "4",
            "balconies": "3",
            "garages": "1 per unit",
            "total_floors": 10,
            "total_units": 42,
            "furnishing": "Semi-furnished",
            "facing": "South-East",
            "land_area": "9 katha",
            "building_area": "128000 sqft",
            "features": "International standard lift\nChildren's play zone\nRooftop garden\nDeep tube well\nModern fire safety system\nCCTV security\nMultipurpose hall",
            "nearby_places": "North South University\nEvercare Hospital\nJamuna Future Park\nISD School\nConvention Point",
            "corporate_office": "Freedom Sales Lounge, Plot 778-805, Road 35 and 37, Block L, Bashundhara R/A, Dhaka",
        },
        {
            "name": f"Skyline Commerce Hub {batch_code}",
            "description": "A mixed-use tower combining office floors, showroom frontage, and serviced apartments with strong cash flow potential for investors.",
            "location": "Agrabad, Chattogram",
            "type": "mixed",
            "property_type": "Commercial + Serviced Apartments",
            "property_for": "Sale",
            "status": "active",
            "construction_status": "Under Construction",
            "start_date": (today - timedelta(days=240)).isoformat(),
            "estimated_end_date": (today + timedelta(days=300)).isoformat(),
            "total_budget": 410000000,
            "progress": 46,
            "unit_size": "950-2200 sqft offices, 1350 sqft serviced flats",
            "transaction_type": "Developer Sale",
            "floor_available_on": "Ground to 16th Floor",
            "bedrooms": "2-3",
            "bathrooms": "2-3",
            "balconies": "1-2",
            "garages": "Basement Parking",
            "total_floors": 16,
            "total_units": 74,
            "furnishing": "Shell and core",
            "facing": "West",
            "land_area": "18 katha",
            "building_area": "214000 sqft",
            "features": "Double-height lobby\nHigh-speed lift\nBackup generator\nFire protection\nConference floor\nRetail frontage\nSmart access control",
            "nearby_places": "Port city business district\nPrivate banks\nHotels\nCorporate offices\nMedical center",
            "corporate_office": "Skyline Commercial Desk, Agrabad C/A, Chattogram",
        },
    ]

    cover_paths = _ensure_demo_project_covers([spec.get("name") or f"Project {idx}" for idx, spec in enumerate(project_specs, start=1)])
    for spec, cover_path in zip(project_specs, cover_paths):
        if cover_path:
            spec["cover_image_path"] = cover_path

    project_ids = []
    for spec in project_specs:
        project_ids.append(
            execute_query(
                "INSERT INTO projects (name, description, location, type, property_type, property_for, status, construction_status, start_date, estimated_end_date, total_budget, progress, unit_size, transaction_type, floor_available_on, bedrooms, bathrooms, balconies, garages, total_floors, total_units, furnishing, facing, land_area, building_area, features, nearby_places, corporate_office, cover_image_path, created_by, created_at, updated_at) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())",
                (
                    spec["name"],
                    spec["description"],
                    spec["location"],
                    spec["type"],
                    spec["property_type"],
                    spec["property_for"],
                    spec["status"],
                    spec["construction_status"],
                    spec["start_date"],
                    spec["estimated_end_date"],
                    spec["total_budget"],
                    spec["progress"],
                    spec["unit_size"],
                    spec["transaction_type"],
                    spec["floor_available_on"],
                    spec["bedrooms"],
                    spec["bathrooms"],
                    spec["balconies"],
                    spec["garages"],
                    spec["total_floors"],
                    spec["total_units"],
                    spec["furnishing"],
                    spec["facing"],
                    spec["land_area"],
                    spec["building_area"],
                    spec["features"],
                    spec["nearby_places"],
                    spec["corporate_office"],
                    spec.get("cover_image_path"),
                    user_id,
                ),
                fetch=False,
            )
        )
    return project_ids


def _insert_investors(investor_types, batch_code):
    investors = []
    for index, inv_type in enumerate(investor_types, start=1):
        phone_tail = 1000 + (index * 17)
        investors.append(
            execute_query(
                "INSERT INTO investors (name, email, phone, address, type_id, company, national_id, bank_name, bank_account, is_active, notes, created_at, updated_at) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 1, %s, NOW(), NOW())",
                (
                    f"{inv_type['name']} Investor {batch_code}-{index}",
                    f"demo.{batch_code.lower()}.{index}@houzez.local",
                    f"01711{phone_tail:06d}"[:11],
                    f"Demo address {index}, Dhaka",
                    inv_type["id"],
                    f"{inv_type['name']} Capital",
                    f"NID-{batch_code}-{index:03d}",
                    "Eastern Bank",
                    f"AC-{batch_code}-{index:04d}",
                    f"Connected demo investor mapped to {inv_type['name']}.",
                ),
                fetch=False,
            )
        )
    return investors


def _insert_contractors(batch_code):
    contractor_specs = [
        ("Prime Build Associates", "Structural Works"),
        ("Metro Finish Studio", "Interior Finishing"),
        ("LiftPro Engineering", "Mechanical and Lift"),
    ]
    contractor_ids = []
    for index, (name, specialization) in enumerate(contractor_specs, start=1):
        contractor_ids.append(
            execute_query(
                "INSERT INTO contractors (name, email, phone, company, specialization, address, rating, is_active, notes, created_at, updated_at) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, 1, %s, NOW(), NOW())",
                (
                    f"{name} {batch_code}",
                    f"contractor.{batch_code.lower()}.{index}@houzez.local",
                    f"01822{(2000 + index * 13):06d}"[:11],
                    f"{name} Ltd.",
                    specialization,
                    f"Site office {index}, Dhaka",
                    4.5 + (index * 0.1),
                    f"Connected demo contractor for batch {batch_code}.",
                ),
                fetch=False,
            )
        )
    return contractor_ids


def _insert_investments(today, batch_code, projects, investors, user_id):
    count = 0
    for index, investor_id in enumerate(investors):
        project_id = projects[index % len(projects)]
        amount = 9000000 + (index * 3500000)
        execute_query(
            "INSERT INTO investments (investor_id, project_id, amount, currency, date, payment_method, reference_no, status, notes, created_by, created_at, updated_at) "
            "VALUES (%s, %s, %s, 'BDT', %s, %s, %s, 'confirmed', %s, %s, NOW(), NOW())",
            (
                investor_id,
                project_id,
                amount,
                (today - timedelta(days=(index + 1) * 28)).isoformat(),
                "bank_transfer" if index % 2 == 0 else "online",
                f"INV-{batch_code}-{index + 1:03d}",
                f"Connected demo investment for batch {batch_code}.",
                user_id,
            ),
            fetch=False,
        )
        count += 1
    return count


def _insert_payment_schedules(today, batch_code, projects, investors):
    count = 0
    statuses = ["paid", "pending", "overdue", "paid", "pending"]
    for investor_index, investor_id in enumerate(investors):
        for installment_no in range(1, 3):
            status = statuses[(investor_index + installment_no - 1) % len(statuses)]
            amount = 1800000 + (investor_index * 225000) + (installment_no * 95000)
            due_date = today + timedelta(days=(investor_index * 14) - (installment_no * 11))
            paid_amount = amount if status == "paid" else 0
            paid_date = due_date.isoformat() if status == "paid" else None
            execute_query(
                "INSERT INTO payment_schedules (investor_id, project_id, installment_no, amount, due_date, paid_date, paid_amount, status, reminder_sent, notes, created_at, updated_at) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())",
                (
                    investor_id,
                    projects[investor_index % len(projects)],
                    installment_no,
                    amount,
                    due_date.isoformat(),
                    paid_date,
                    paid_amount,
                    status,
                    1 if status == "overdue" else 0,
                    f"Installment {installment_no} for connected demo batch {batch_code}.",
                ),
                fetch=False,
            )
            count += 1
    return count


def _insert_cost_items(today, batch_code, projects, cost_categories, user_id):
    count = 0
    units = ["lot", "bag", "sqft", "kg", "floor", "set", "trip"]
    statuses = ["approved", "paid", "pending", "delivered"]
    for index, category in enumerate(cost_categories, start=1):
        project_id = projects[(index - 1) % len(projects)]
        quantity = 10 + (index * 2)
        unit_price = 1200 + (index * 95)
        estimated = quantity * unit_price
        actual = estimated - (index * 250 if index % 3 else 0)
        execute_query(
            "INSERT INTO cost_items (name, project_id, category_id, description, quantity, unit, unit_price, estimated_amount, actual_amount, currency, date, vendor, invoice_no, status, notes, created_by, created_at, updated_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'BDT', %s, %s, %s, %s, %s, %s, NOW(), NOW())",
            (
                f"{category['name']} Allocation {batch_code}-{index:02d}",
                project_id,
                category["id"],
                f"Demo cost record generated for category {category['name']}.",
                quantity,
                units[(index - 1) % len(units)],
                unit_price,
                estimated,
                max(actual, 0),
                (today - timedelta(days=index * 3)).isoformat(),
                f"Vendor {index} for {category['name']}",
                f"COST-{batch_code}-{index:03d}",
                statuses[(index - 1) % len(statuses)],
                f"Connected demo cost item for batch {batch_code}.",
                user_id,
            ),
            fetch=False,
        )
        count += 1
    return count


def _insert_contractor_payments(today, batch_code, projects, contractors, user_id):
    count = 0
    for index, contractor_id in enumerate(contractors, start=1):
        execute_query(
            "INSERT INTO contractor_payments (contractor_id, project_id, amount, currency, date, invoice_no, description, status, notes, created_by, created_at, updated_at) "
            "VALUES (%s, %s, %s, 'BDT', %s, %s, %s, %s, %s, %s, NOW(), NOW())",
            (
                contractor_id,
                projects[(index - 1) % len(projects)],
                850000 + (index * 275000),
                (today - timedelta(days=index * 19)).isoformat(),
                f"CP-{batch_code}-{index:03d}",
                f"Milestone payment for contractor batch {batch_code}.",
                "paid" if index != len(contractors) else "approved",
                f"Connected demo contractor payment {index}.",
                user_id,
            ),
            fetch=False,
        )
        count += 1
    return count


def _insert_cash_transactions(today, batch_code, projects, investors, contractors, user_id):
    rows = [
        (projects[0], investors[0], None, "sale", "inflow", 12400000, (today - timedelta(days=6)).isoformat(), "Unit Buyer - Sohana Rahman", f"SALE-{batch_code}-01", "bank_transfer", "Apartment booking collection"),
        (projects[0], None, None, "buy", "outflow", 3900000, (today - timedelta(days=22)).isoformat(), "Land Seller Consortium", f"BUY-{batch_code}-02", "cheque", "Advance payment for adjacent plot"),
        (projects[1], None, contractors[1], "expense", "outflow", 640000, (today - timedelta(days=4)).isoformat(), "Marketing Agency", f"EXP-{batch_code}-03", "online", "Campaign spend for launch"),
        (projects[2], investors[2], None, "refund_in", "inflow", 420000, (today - timedelta(days=2)).isoformat(), "Utility Rebate", f"REF-{batch_code}-04", "bank_transfer", "Refund from service provider"),
        (projects[2], None, None, "other_outflow", "outflow", 285000, today.isoformat(), "Legal Desk", f"LEG-{batch_code}-05", "cash", "Registration and legal filing"),
    ]

    count = 0
    for row in rows:
        execute_query(
            "INSERT INTO cash_transactions (project_id, investor_id, contractor_id, entry_type, direction, amount, currency, tx_date, counterparty, reference_no, payment_method, status, source_table, notes, created_by, created_at, updated_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, 'BDT', %s, %s, %s, %s, 'confirmed', 'manual', %s, %s, NOW(), NOW())",
            row + (user_id,),
            fetch=False,
        )
        count += 1
    return count


def _insert_email_logs(today, batch_code, projects, investors):
    count = 0
    for index, investor_id in enumerate(investors, start=1):
        project_name = execute_query("SELECT name FROM projects WHERE id=%s", (projects[(index - 1) % len(projects)],))[0]["name"]
        investor = execute_query("SELECT name, email FROM investors WHERE id=%s", (investor_id,))[0]
        status = "sent" if index % 4 else "failed"
        error = None if status == "sent" else "SMTP sandbox failure for demo purposes"
        body = (
            f"Dear {investor['name']},\n\n"
            f"This is a connected demo email log for {project_name}. "
            f"Please review installment plan batch {batch_code}.\n\n"
            "Regards,\nHouzez CRM"
        )
        execute_query(
            "INSERT INTO email_logs (investor_id, to_email, subject, body, status, error, sent_at) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (
                investor_id,
                investor["email"],
                f"{project_name} update {batch_code}",
                body,
                status,
                error,
                (today - timedelta(days=index)).isoformat(),
            ),
            fetch=False,
        )
        count += 1
    return count


def _insert_audit_logs(batch_code, user_id, project_count, investor_count, cost_count):
    logs = [
        ("CREATE", "demo_workspace", f"Seeded connected demo workspace {batch_code} with {project_count} projects."),
        ("CREATE", "investor", f"Created {investor_count} demo investors for batch {batch_code}."),
        ("CREATE", "cost_item", f"Generated {cost_count} linked cost items for batch {batch_code}."),
    ]
    count = 0
    for action, entity_type, description in logs:
        execute_query(
            "INSERT INTO audit_logs (user_id, action, description, entity_type, ip_address, created_at) VALUES (%s, %s, %s, %s, %s, NOW())",
            (user_id, action, description, entity_type, "desktop-demo-seed"),
            fetch=False,
        )
        count += 1
    return count
