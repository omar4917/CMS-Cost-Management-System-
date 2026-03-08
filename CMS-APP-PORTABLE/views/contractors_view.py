"""
Contractors View for CMS Desktop App.
Modern contractor management with profile and payment tabs.
"""

from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk

from core.database import execute_query
from core.desktop_utils import as_float, format_date, pick_column


class ContractorsView(ctk.CTkFrame):
    def __init__(self, parent, user):
        super().__init__(parent, fg_color="transparent")
        self.user = user
        self.payment_date_col = pick_column("contractor_payments", "date", "payment_date", fallback="date")
        self.build_ui()
        self.refresh_stats()
        self.load_contractors()

    def build_ui(self):
        hero = ctk.CTkFrame(
            self,
            fg_color="#0d1630",
            corner_radius=22,
            border_width=1,
            border_color="#233154",
        )
        hero.pack(fill="x", pady=(0, 14))

        hero_header = ctk.CTkFrame(hero, fg_color="transparent")
        hero_header.pack(fill="x", padx=22, pady=(18, 8))

        title_col = ctk.CTkFrame(hero_header, fg_color="transparent")
        title_col.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(
            title_col,
            text="Contractor Command",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="#f8fafc",
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_col,
            text="Manage vendors, keep payments visible, and remove stale profiles cleanly.",
            font=ctk.CTkFont(size=13),
            text_color="#8ea3c7",
        ).pack(anchor="w", pady=(4, 0))

        ctk.CTkButton(
            hero_header,
            text="+ New Contractor",
            height=42,
            corner_radius=12,
            fg_color="#4f8cff",
            hover_color="#3578f6",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: self.open_contractor_dialog(),
        ).pack(side="right")

        stats_row = ctk.CTkFrame(hero, fg_color="transparent")
        stats_row.pack(fill="x", padx=22, pady=(4, 18))

        self.stats_labels = {}
        for key, title, color in [
            ("contractors", "Active Profiles", "#4f8cff"),
            ("payments", "Recorded Payments", "#27d3a2"),
            ("value", "Paid Out", "#ffb347"),
        ]:
            card = ctk.CTkFrame(
                stats_row,
                fg_color="#111d39",
                corner_radius=16,
                border_width=1,
                border_color="#233154",
                height=92,
            )
            card.pack(side="left", fill="x", expand=True, padx=(0, 10) if key != "value" else 0)
            card.pack_propagate(False)
            ctk.CTkLabel(card, text=title, text_color="#7e93ba", font=ctk.CTkFont(size=12)).pack(
                anchor="w", padx=16, pady=(14, 0)
            )
            value_label = ctk.CTkLabel(
                card,
                text="—",
                text_color=color,
                font=ctk.CTkFont(size=24, weight="bold"),
            )
            value_label.pack(anchor="w", padx=16, pady=(6, 0))
            self.stats_labels[key] = value_label

        self.tabview = ctk.CTkTabview(
            self,
            fg_color="#0c1427",
            corner_radius=20,
            segmented_button_fg_color="#14203b",
            segmented_button_selected_color="#4f8cff",
            segmented_button_selected_hover_color="#3578f6",
            segmented_button_unselected_color="#14203b",
            text_color="#d9e4ff",
            border_width=1,
            border_color="#1f2a45",
        )
        self.tabview.pack(fill="both", expand=True)
        self.tabview.add("Profiles")
        self.tabview.add("Payments")
        self.tabview.configure(command=self.on_tab_change)

        self.tab1 = self.tabview.tab("Profiles")
        self.tab2 = self.tabview.tab("Payments")

        self._build_profiles_tab()
        self._build_payments_tab()

    def _build_profiles_tab(self):
        ctrl = ctk.CTkFrame(self.tab1, fg_color="transparent")
        ctrl.pack(fill="x", padx=18, pady=(18, 10))

        ctk.CTkLabel(
            ctrl,
            text="Profiles",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#f8fafc",
        ).pack(side="left")
        ctk.CTkLabel(
            ctrl,
            text="Edit details or delete a contractor together with their payment history.",
            font=ctk.CTkFont(size=12),
            text_color="#7789ac",
        ).pack(side="left", padx=(12, 0))

        ctk.CTkButton(
            ctrl,
            text="+ Add Contractor",
            fg_color="#4f8cff",
            hover_color="#3578f6",
            corner_radius=10,
            height=34,
            command=lambda: self.open_contractor_dialog(),
        ).pack(side="right")

        self.prof_table = ctk.CTkScrollableFrame(
            self.tab1,
            fg_color="#0d1630",
            corner_radius=18,
            border_width=1,
            border_color="#1f2a45",
        )
        self.prof_table.pack(fill="both", expand=True, padx=18, pady=(0, 18))

    def _build_payments_tab(self):
        ctrl = ctk.CTkFrame(self.tab2, fg_color="transparent")
        ctrl.pack(fill="x", padx=18, pady=(18, 10))

        ctk.CTkLabel(
            ctrl,
            text="Payments",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#f8fafc",
        ).pack(side="left")
        ctk.CTkLabel(
            ctrl,
            text="Track vendor payouts with project and invoice context.",
            font=ctk.CTkFont(size=12),
            text_color="#7789ac",
        ).pack(side="left", padx=(12, 0))

        ctk.CTkButton(
            ctrl,
            text="+ Record Payment",
            fg_color="#27d3a2",
            hover_color="#16b48b",
            text_color="#082a25",
            corner_radius=10,
            height=34,
            command=self.open_payment_dialog,
        ).pack(side="right")

        self.pay_table = ctk.CTkScrollableFrame(
            self.tab2,
            fg_color="#0d1630",
            corner_radius=18,
            border_width=1,
            border_color="#1f2a45",
        )
        self.pay_table.pack(fill="both", expand=True, padx=18, pady=(0, 18))

    def refresh_stats(self):
        try:
            contractors = execute_query("SELECT COUNT(*) AS total FROM contractors WHERE is_active=1")
            payments = execute_query("SELECT COUNT(*) AS total, COALESCE(SUM(amount), 0) AS value FROM contractor_payments")
            self.stats_labels["contractors"].configure(text=str(contractors[0]["total"] or 0))
            self.stats_labels["payments"].configure(text=str(payments[0]["total"] or 0))
            self.stats_labels["value"].configure(text=f"BDT {as_float(payments[0]['value']):,.0f}")
        except Exception:
            pass

    def on_tab_change(self):
        self.refresh_stats()
        if self.tabview.get() == "Profiles":
            self.load_contractors()
        else:
            self.load_payments()

    def load_contractors(self):
        for widget in self.prof_table.winfo_children():
            widget.destroy()

        try:
            contractors = execute_query("SELECT * FROM contractors ORDER BY name ASC")
        except Exception as exc:
            ctk.CTkLabel(self.prof_table, text=f"Error: {exc}", text_color="#ef4444").pack(pady=20)
            return

        if not contractors:
            self._empty_state(self.prof_table, "No contractors yet", "Create your first contractor profile to get started.")
            return

        for contractor in contractors:
            row = ctk.CTkFrame(
                self.prof_table,
                fg_color="#111d39",
                corner_radius=16,
                border_width=1,
                border_color="#223356",
            )
            row.pack(fill="x", padx=8, pady=6)

            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(side="left", fill="both", expand=True, padx=16, pady=14)

            ctk.CTkLabel(
                info,
                text=contractor.get("name", ""),
                font=ctk.CTkFont(size=15, weight="bold"),
                text_color="#f8fafc",
            ).pack(anchor="w")

            meta = "  |  ".join(
                value
                for value in [
                    contractor.get("company") or "No company",
                    contractor.get("specialization") or "General",
                    contractor.get("phone") or "No phone",
                    contractor.get("email") or "No email",
                ]
                if value
            )
            ctk.CTkLabel(
                info,
                text=meta,
                font=ctk.CTkFont(size=12),
                text_color="#8aa0c8",
                wraplength=760,
                justify="left",
            ).pack(anchor="w", pady=(6, 0))

            actions = ctk.CTkFrame(row, fg_color="transparent")
            actions.pack(side="right", padx=14, pady=14)

            ctk.CTkButton(
                actions,
                text="Edit",
                width=64,
                height=32,
                corner_radius=10,
                fg_color="#203150",
                hover_color="#2b426d",
                command=lambda item=contractor: self.open_contractor_dialog(item),
            ).pack(side="left", padx=4)
            ctk.CTkButton(
                actions,
                text="Delete",
                width=70,
                height=32,
                corner_radius=10,
                fg_color="#261522",
                hover_color="#4a1d2d",
                text_color="#ff7a90",
                command=lambda item=contractor: self.delete_contractor(item),
            ).pack(side="left", padx=4)

    def load_payments(self):
        for widget in self.pay_table.winfo_children():
            widget.destroy()

        try:
            payments = execute_query(
                f"""
                SELECT cp.id,
                       cp.amount,
                       cp.{self.payment_date_col} AS payment_date,
                       cp.description,
                       cp.invoice_no,
                       cp.status,
                       c.name AS contractor_name,
                       p.name AS project_name
                FROM contractor_payments cp
                JOIN contractors c ON cp.contractor_id = c.id
                LEFT JOIN projects p ON cp.project_id = p.id
                ORDER BY cp.{self.payment_date_col} DESC, cp.created_at DESC
                LIMIT 50
                """
            )
        except Exception as exc:
            ctk.CTkLabel(self.pay_table, text=f"Error: {exc}", text_color="#ef4444").pack(pady=20)
            return

        if not payments:
            self._empty_state(self.pay_table, "No contractor payments", "Record a payment to populate the payout ledger.")
            return

        for payment in payments:
            row = ctk.CTkFrame(
                self.pay_table,
                fg_color="#111d39",
                corner_radius=16,
                border_width=1,
                border_color="#223356",
            )
            row.pack(fill="x", padx=8, pady=6)

            top = ctk.CTkFrame(row, fg_color="transparent")
            top.pack(fill="x", padx=16, pady=(14, 6))
            ctk.CTkLabel(
                top,
                text=payment.get("contractor_name", "Unknown contractor"),
                font=ctk.CTkFont(size=15, weight="bold"),
                text_color="#f8fafc",
            ).pack(side="left")
            ctk.CTkLabel(
                top,
                text=f"BDT {as_float(payment.get('amount')):,.0f}",
                font=ctk.CTkFont(size=15, weight="bold"),
                text_color="#27d3a2",
            ).pack(side="right")

            meta = ctk.CTkFrame(row, fg_color="transparent")
            meta.pack(fill="x", padx=16, pady=(0, 14))
            details = [
                f"Date: {format_date(payment.get('payment_date'))}",
                f"Project: {payment.get('project_name') or 'N/A'}",
                f"Invoice: {payment.get('invoice_no') or 'N/A'}",
                f"Status: {(payment.get('status') or 'pending').upper()}",
            ]
            if payment.get("description"):
                details.append(f"Note: {payment['description']}")
            ctk.CTkLabel(
                meta,
                text="  |  ".join(details),
                font=ctk.CTkFont(size=12),
                text_color="#8aa0c8",
                wraplength=980,
                justify="left",
            ).pack(anchor="w")

    def delete_contractor(self, contractor):
        name = contractor.get("name", "this contractor")
        if not messagebox.askyesno(
            "Delete Contractor",
            f"Delete {name} and every payment linked to this contractor?",
        ):
            return

        try:
            execute_query("DELETE FROM contractor_payments WHERE contractor_id=%s", (contractor["id"],), fetch=False)
            execute_query("DELETE FROM contractors WHERE id=%s", (contractor["id"],), fetch=False)
            execute_query(
                "INSERT INTO audit_logs (user_id, action, entity_type, entity_id, description, created_at) "
                "VALUES (%s, 'delete', 'contractor', %s, %s, NOW())",
                (self.user.get("id"), contractor["id"], f"Deleted contractor {name} from desktop app"),
                fetch=False,
            )
            self.refresh_stats()
            self.load_contractors()
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def open_contractor_dialog(self, contractor=None):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Edit Contractor" if contractor else "Add Contractor")
        dialog.geometry("460x560")
        dialog.configure(fg_color="#0b1327")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        ctk.CTkLabel(
            dialog,
            text="Contractor Profile",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#f8fafc",
        ).pack(pady=(24, 10))

        form = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=28)

        entries = {}

        def add_field(label, key, placeholder=""):
            ctk.CTkLabel(form, text=label, text_color="#9bb0d5", font=ctk.CTkFont(size=12, weight="bold")).pack(
                anchor="w", pady=(10, 4)
            )
            entry = ctk.CTkEntry(
                form,
                height=40,
                fg_color="#101b35",
                border_color="#233154",
                corner_radius=10,
                placeholder_text=placeholder,
            )
            if contractor and contractor.get(key):
                entry.insert(0, str(contractor.get(key)))
            entry.pack(fill="x")
            entries[key] = entry

        add_field("Name *", "name", "Prime Build Associates")
        add_field("Company", "company", "Vendor company")
        add_field("Specialization", "specialization", "Structural, electrical, finishing...")
        add_field("Phone", "phone", "01XXXXXXXXX")
        add_field("Email", "email", "contractor@example.com")

        def save():
            name = entries["name"].get().strip()
            if not name:
                return messagebox.showerror("Error", "Contractor name is required.")

            values = (
                name,
                entries["company"].get().strip(),
                entries["specialization"].get().strip(),
                entries["phone"].get().strip(),
                entries["email"].get().strip(),
            )

            try:
                if contractor:
                    execute_query(
                        "UPDATE contractors SET name=%s, company=%s, specialization=%s, phone=%s, email=%s, updated_at=NOW() WHERE id=%s",
                        values + (contractor["id"],),
                        fetch=False,
                    )
                else:
                    execute_query(
                        "INSERT INTO contractors (name, company, specialization, phone, email, is_active, created_at, updated_at) "
                        "VALUES (%s, %s, %s, %s, %s, 1, NOW(), NOW())",
                        values,
                        fetch=False,
                    )
                dialog.destroy()
                self.refresh_stats()
                self.load_contractors()
            except Exception as exc:
                messagebox.showerror("Error", str(exc))

        footer = ctk.CTkFrame(dialog, fg_color="transparent")
        footer.pack(fill="x", padx=28, pady=(8, 22))
        ctk.CTkButton(
            footer,
            text="Cancel",
            fg_color="#182748",
            hover_color="#223660",
            corner_radius=10,
            height=38,
            command=dialog.destroy,
        ).pack(side="left")
        ctk.CTkButton(
            footer,
            text="Save Contractor",
            fg_color="#4f8cff",
            hover_color="#3578f6",
            corner_radius=10,
            height=38,
            command=save,
        ).pack(side="right")

    def open_payment_dialog(self):
        try:
            contractors = execute_query("SELECT id, name FROM contractors ORDER BY name")
            projects = execute_query("SELECT id, name FROM projects ORDER BY name")
        except Exception:
            return messagebox.showerror("Error", "Could not load contractors or projects.")

        if not contractors:
            return messagebox.showwarning("Warning", "Add a contractor first.")

        dialog = ctk.CTkToplevel(self)
        dialog.title("Record Contractor Payment")
        dialog.geometry("500x620")
        dialog.configure(fg_color="#0b1327")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        ctk.CTkLabel(
            dialog,
            text="Record Contractor Payment",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#f8fafc",
        ).pack(pady=(24, 10))

        form = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=28)

        contractor_var = ctk.StringVar(value=f"{contractors[0]['name']} (ID: {contractors[0]['id']})")
        project_options = ["None"] + [f"{project['name']} (ID: {project['id']})" for project in projects]
        project_var = ctk.StringVar(value="None")

        for label, variable, values in [
            ("Contractor *", contractor_var, [f"{item['name']} (ID: {item['id']})" for item in contractors]),
            ("Project", project_var, project_options),
        ]:
            ctk.CTkLabel(form, text=label, text_color="#9bb0d5", font=ctk.CTkFont(size=12, weight="bold")).pack(
                anchor="w", pady=(10, 4)
            )
            ctk.CTkOptionMenu(
                form,
                variable=variable,
                values=values,
                fg_color="#101b35",
                button_color="#233154",
                button_hover_color="#31446b",
                height=40,
                corner_radius=10,
            ).pack(fill="x")

        entries = {}
        for label, key, default in [
            ("Amount (BDT) *", "amount", ""),
            ("Payment Date (YYYY-MM-DD) *", "date", datetime.now().strftime("%Y-%m-%d")),
            ("Invoice Number", "invoice_no", ""),
            ("Description", "description", ""),
        ]:
            ctk.CTkLabel(form, text=label, text_color="#9bb0d5", font=ctk.CTkFont(size=12, weight="bold")).pack(
                anchor="w", pady=(10, 4)
            )
            entry = ctk.CTkEntry(
                form,
                height=40,
                fg_color="#101b35",
                border_color="#233154",
                corner_radius=10,
            )
            if default:
                entry.insert(0, default)
            entry.pack(fill="x")
            entries[key] = entry

        def save():
            amount = entries["amount"].get().strip()
            payment_date = entries["date"].get().strip()
            if not amount or not payment_date:
                return messagebox.showerror("Error", "Amount and payment date are required.")

            contractor_id = contractor_var.get().split("ID: ")[1].rstrip(")")
            project_value = project_var.get()
            project_id = None if project_value == "None" else project_value.split("ID: ")[1].rstrip(")")

            try:
                execute_query(
                    f"INSERT INTO contractor_payments (contractor_id, project_id, amount, currency, {self.payment_date_col}, invoice_no, description, status, created_by, created_at, updated_at) "
                    f"VALUES (%s, %s, %s, 'BDT', %s, %s, %s, 'paid', %s, NOW(), NOW())",
                    (
                        contractor_id,
                        project_id,
                        amount,
                        payment_date,
                        entries["invoice_no"].get().strip(),
                        entries["description"].get().strip(),
                        self.user.get("id"),
                    ),
                    fetch=False,
                )
                execute_query(
                    "INSERT INTO audit_logs (user_id, action, entity_type, description, created_at) VALUES (%s, 'create', 'contractor_payment', %s, NOW())",
                    (
                        self.user.get("id"),
                        f"Recorded contractor payment of {amount} for contractor {contractor_id}",
                    ),
                    fetch=False,
                )
                dialog.destroy()
                self.refresh_stats()
                self.load_payments()
            except Exception as exc:
                messagebox.showerror("Error", str(exc))

        footer = ctk.CTkFrame(dialog, fg_color="transparent")
        footer.pack(fill="x", padx=28, pady=(8, 22))
        ctk.CTkButton(
            footer,
            text="Cancel",
            fg_color="#182748",
            hover_color="#223660",
            corner_radius=10,
            height=38,
            command=dialog.destroy,
        ).pack(side="left")
        ctk.CTkButton(
            footer,
            text="Save Payment",
            fg_color="#27d3a2",
            hover_color="#16b48b",
            text_color="#082a25",
            corner_radius=10,
            height=38,
            command=save,
        ).pack(side="right")

    def _empty_state(self, parent, title, subtitle):
        wrap = ctk.CTkFrame(parent, fg_color="transparent")
        wrap.pack(expand=True, pady=70)
        ctk.CTkLabel(wrap, text=title, font=ctk.CTkFont(size=18, weight="bold"), text_color="#d8e4ff").pack()
        ctk.CTkLabel(wrap, text=subtitle, font=ctk.CTkFont(size=12), text_color="#6e84ac").pack(pady=(6, 0))
