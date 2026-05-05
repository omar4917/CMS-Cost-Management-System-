"""
Investors view for the desktop app.
"""

from tkinter import messagebox

import customtkinter as ctk

from core.database import execute_query
from core.recycle_bin import recycle_and_delete, recycle_and_delete_many


def _safe_float(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


class InvestorsView(ctk.CTkFrame):
    def __init__(self, parent, user):
        super().__init__(parent, fg_color="transparent")
        self.user = user
        self.investor_types = []
        self.build_ui()
        self.load_types()
        self.load_data()

    def build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(5, 18))

        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left")
        ctk.CTkLabel(title_frame, text="Investors", font=ctk.CTkFont(size=24, weight="bold"), text_color="#f1f5f9").pack(side="left")
        ctk.CTkButton(
            header,
            text="+ Add Investor",
            fg_color="#3b82f6",
            hover_color="#2563eb",
            corner_radius=10,
            height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.open_add,
        ).pack(side="right")

        search_frame = ctk.CTkFrame(self, fg_color="#111827", corner_radius=12, border_width=1, border_color="#1e293b")
        search_frame.pack(fill="x", pady=(0, 15))
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.load_data())
        ctk.CTkEntry(
            search_frame,
            placeholder_text="Search by name, email, company, or type...",
            height=42,
            corner_radius=10,
            fg_color="transparent",
            border_width=0,
            textvariable=self.search_var,
            font=ctk.CTkFont(size=13),
            text_color="#e2e8f0",
            placeholder_text_color="#475569",
        ).pack(fill="x", padx=12, pady=6)

        self.table_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="#111827",
            corner_radius=14,
            border_width=1,
            border_color="#1e293b",
            scrollbar_button_color="#1e293b",
            scrollbar_button_hover_color="#334155",
        )
        self.table_frame.pack(fill="both", expand=True)

    def load_types(self):
        try:
            self.investor_types = execute_query("SELECT * FROM investor_types ORDER BY name")
        except Exception:
            self.investor_types = []

    def load_data(self):
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        query = (
            "SELECT i.*, it.name AS type_name, it.color AS type_color "
            "FROM investors i LEFT JOIN investor_types it ON i.type_id = it.id "
            "WHERE 1=1"
        )
        params = []
        search = self.search_var.get().strip()
        if search:
            query += " AND (i.name LIKE %s OR i.email LIKE %s OR i.company LIKE %s OR it.name LIKE %s)"
            params.extend([f"%{search}%"] * 4)
        query += " ORDER BY i.created_at DESC"

        try:
            investors = execute_query(query, params)
        except Exception as exc:
            ctk.CTkLabel(self.table_frame, text=f"Error: {exc}", text_color="#ef4444", font=ctk.CTkFont(size=13)).pack(pady=20)
            return

        if not investors:
            ctk.CTkLabel(self.table_frame, text="No investors found", font=ctk.CTkFont(size=16, weight="bold"), text_color="#475569").pack(pady=60)
            return

        header = ctk.CTkFrame(self.table_frame, fg_color="#0c1222", corner_radius=8)
        header.pack(fill="x", padx=8, pady=(8, 4))
        self._configure_columns(header)
        for idx, label in enumerate(["Name", "Email", "Phone", "Type", "Status", "Actions"]):
            ctk.CTkLabel(header, text=label.upper(), font=ctk.CTkFont(size=10, weight="bold"), text_color="#475569", anchor="w").grid(row=0, column=idx, sticky="ew", padx=8, pady=10)

        for investor in investors:
            row = ctk.CTkFrame(self.table_frame, fg_color="#0f172a", corner_radius=6)
            row.pack(fill="x", padx=8, pady=1)
            self._configure_columns(row)
            row.bind("<Enter>", lambda _e, r=row: r.configure(fg_color="#1e293b"))
            row.bind("<Leave>", lambda _e, r=row: r.configure(fg_color="#0f172a"))

            type_color = investor.get("type_color") or "#3b82f6"
            status_color = "#10b981" if investor.get("is_active") else "#ef4444"
            values = [
                investor.get("name") or "",
                investor.get("email") or "-",
                investor.get("phone") or "-",
                investor.get("type_name") or "N/A",
                "Active" if investor.get("is_active") else "Inactive",
            ]
            for idx, value in enumerate(values):
                color = "#e2e8f0" if idx == 0 else "#94a3b8"
                if idx == 3:
                    color = type_color
                if idx == 4:
                    color = status_color
                font = ctk.CTkFont(size=13, weight="bold") if idx in {0, 4} else ctk.CTkFont(size=12)
                ctk.CTkLabel(row, text=value, text_color=color, font=font, anchor="w").grid(row=0, column=idx, sticky="ew", padx=8, pady=10)

            btn_frame = ctk.CTkFrame(row, fg_color="transparent")
            btn_frame.grid(row=0, column=5, sticky="e", padx=8, pady=8)
            ctk.CTkButton(btn_frame, text="View", width=42, height=28, corner_radius=6, fg_color="#1e293b", hover_color="#334155", font=ctk.CTkFont(size=11), border_width=1, border_color="#334155", command=lambda item=investor: self.view_summary(item)).pack(side="left", padx=2)
            ctk.CTkButton(btn_frame, text="Edit", width=42, height=28, corner_radius=6, fg_color="#1e293b", hover_color="#334155", font=ctk.CTkFont(size=11), border_width=1, border_color="#334155", command=lambda item=investor: self.open_edit(item)).pack(side="left", padx=2)
            ctk.CTkButton(btn_frame, text="Del", width=38, height=28, corner_radius=6, fg_color="transparent", hover_color="#7f1d1d", text_color="#ef4444", font=ctk.CTkFont(size=11), border_width=1, border_color="#7f1d1d", command=lambda item_id=investor["id"]: self.delete_investor(item_id)).pack(side="left", padx=2)
            self._bind_click(row, lambda _e, item=investor: self.view_summary(item))

        footer = ctk.CTkFrame(self.table_frame, fg_color="transparent")
        footer.pack(fill="x", padx=10, pady=(8, 4))
        ctk.CTkLabel(footer, text=f"Showing {len(investors)} investor{'s' if len(investors) != 1 else ''}", font=ctk.CTkFont(size=11), text_color="#475569").pack(side="left")

    def _configure_columns(self, frame):
        specs = [(0, 2, 170), (1, 2, 180), (2, 1, 120), (3, 1, 120), (4, 1, 90), (5, 0, 140)]
        for column, weight, minsize in specs:
            frame.grid_columnconfigure(column, weight=weight, minsize=minsize)

    def _bind_click(self, widget, callback):
        if isinstance(widget, ctk.CTkButton):
            return
        widget.bind("<Button-1>", callback)
        for child in widget.winfo_children():
            self._bind_click(child, callback)

    def view_summary(self, investor):
        dialog = ctk.CTkToplevel(self)
        dialog.title(investor["name"])
        dialog.geometry("700x700")
        dialog.configure(fg_color="#0f172a")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        ctk.CTkLabel(dialog, text=investor["name"], font=ctk.CTkFont(size=24, weight="bold"), text_color="white").pack(anchor="w", padx=28, pady=(24, 4))
        ctk.CTkLabel(dialog, text=investor.get("type_name") or "Investor", font=ctk.CTkFont(size=12), text_color=investor.get("type_color") or "#64748b").pack(anchor="w", padx=28)

        body = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=(16, 10))

        invested = execute_query("SELECT COALESCE(SUM(amount), 0) AS total FROM investments WHERE investor_id=%s AND status='confirmed'", (investor["id"],))
        paid = execute_query("SELECT COALESCE(SUM(amount), 0) AS total FROM payment_schedules WHERE investor_id=%s AND status='paid'", (investor["id"],))
        total_invested = _safe_float(invested[0]["total"] if invested else 0)
        total_paid = _safe_float(paid[0]["total"] if paid else 0)

        stats = ctk.CTkFrame(body, fg_color="transparent")
        stats.pack(fill="x")
        for idx in range(3):
            stats.grid_columnconfigure(idx, weight=1)
        for idx, (label, value, color) in enumerate(
            [
                ("Total Invested", f"BDT {total_invested:,.0f}", "#10b981"),
                ("Total Paid", f"BDT {total_paid:,.0f}", "#3b82f6"),
                ("Unpaid / Due", f"BDT {max(total_invested - total_paid, 0):,.0f}", "#ef4444"),
            ]
        ):
            card = ctk.CTkFrame(stats, fg_color="#111827", corner_radius=12, border_width=1, border_color="#1e293b")
            card.grid(row=0, column=idx, padx=5, sticky="nsew")
            ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=18, weight="bold"), text_color=color).pack(pady=(15, 3), padx=10)
            ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=11), text_color="#64748b").pack(pady=(0, 12))

        info = ctk.CTkFrame(body, fg_color="#111827", corner_radius=16, border_width=1, border_color="#1e293b")
        info.pack(fill="x", pady=(14, 0))
        for label, value in [
            ("Email", investor.get("email") or "-"),
            ("Phone", investor.get("phone") or "-"),
            ("Company", investor.get("company") or "-"),
            ("National ID", investor.get("national_id") or "-"),
            ("Bank Name", investor.get("bank_name") or "-"),
            ("Bank Account", investor.get("bank_account") or "-"),
            ("Address", investor.get("address") or "-"),
            ("Status", "Active" if investor.get("is_active") else "Inactive"),
        ]:
            row = ctk.CTkFrame(info, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=8)
            ctk.CTkLabel(row, text=label, width=120, anchor="w", font=ctk.CTkFont(size=12, weight="bold"), text_color="#94a3b8").pack(side="left")
            ctk.CTkLabel(row, text=value, font=ctk.CTkFont(size=12), text_color="#e2e8f0", wraplength=420, justify="left").pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(body, text="Notes / Comment", font=ctk.CTkFont(size=14, weight="bold"), text_color="white").pack(anchor="w", pady=(14, 6))
        notes_box = ctk.CTkTextbox(body, height=120, fg_color="#111827", border_color="#1e293b", border_width=1, corner_radius=12, wrap="word")
        notes_box.pack(fill="x")
        notes_box.insert("1.0", str(investor.get("notes") or "No notes saved."))
        notes_box.configure(state="disabled")

        history = execute_query(
            "SELECT inv.amount, inv.date, inv.payment_method, p.name AS project_name "
            "FROM investments inv LEFT JOIN projects p ON inv.project_id = p.id "
            "WHERE inv.investor_id=%s ORDER BY inv.date DESC LIMIT 10",
            (investor["id"],),
        )
        if history:
            ctk.CTkLabel(body, text="Investment History", font=ctk.CTkFont(size=14, weight="bold"), text_color="white").pack(anchor="w", pady=(14, 6))
            for record in history:
                row = ctk.CTkFrame(body, fg_color="#111827", corner_radius=8, border_width=1, border_color="#1e293b")
                row.pack(fill="x", pady=2)
                ctk.CTkLabel(row, text=record.get("project_name") or "-", font=ctk.CTkFont(size=12), text_color="#e2e8f0", width=200, anchor="w").pack(side="left", padx=10, pady=8)
                ctk.CTkLabel(row, text=f"BDT {_safe_float(record.get('amount')):,.0f}", font=ctk.CTkFont(size=12, weight="bold"), text_color="#10b981", width=130, anchor="w").pack(side="left", padx=5)
                ctk.CTkLabel(row, text=str(record.get("date") or "-"), font=ctk.CTkFont(size=11), text_color="#64748b", width=120, anchor="w").pack(side="left", padx=5)
                ctk.CTkLabel(row, text=str(record.get("payment_method") or "-").replace("_", " "), font=ctk.CTkFont(size=11), text_color="#475569").pack(side="right", padx=10)

        footer = ctk.CTkFrame(dialog, fg_color="transparent")
        footer.pack(fill="x", padx=24, pady=(0, 20))
        ctk.CTkButton(footer, text="Close", fg_color="#1e293b", hover_color="#334155", height=38, corner_radius=10, command=dialog.destroy).pack(side="left")
        ctk.CTkButton(footer, text="Edit Investor", fg_color="#3b82f6", hover_color="#2563eb", height=38, corner_radius=10, command=lambda: [dialog.destroy(), self.open_edit(investor)]).pack(side="right")

    def open_add(self):
        self._open_dialog(None)

    def open_edit(self, investor):
        self._open_dialog(investor)

    def _open_dialog(self, investor):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Edit Investor" if investor else "Add Investor")
        dialog.geometry("620x760")
        dialog.configure(fg_color="#0f172a")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Edit Investor" if investor else "Add Investor", font=ctk.CTkFont(size=20, weight="bold"), text_color="white").pack(pady=(20, 15))
        form = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=30)

        fields = {}

        def add_field(label, key, default=""):
            ctk.CTkLabel(form, text=label, font=ctk.CTkFont(size=12, weight="bold"), text_color="#94a3b8").pack(anchor="w", pady=(10, 3))
            entry = ctk.CTkEntry(form, height=40, fg_color="#1e293b", border_color="#334155", corner_radius=10, font=ctk.CTkFont(size=13))
            value = str(investor.get(key, "") or default) if investor else str(default or "")
            if value:
                entry.insert(0, value)
            entry.pack(fill="x")
            fields[key] = entry

        add_field("Full Name *", "name")
        add_field("Email", "email")
        add_field("Phone", "phone")
        add_field("Company", "company")
        add_field("National ID", "national_id")
        add_field("Bank Name", "bank_name")
        add_field("Bank Account", "bank_account")

        ctk.CTkLabel(form, text="Investor Type", font=ctk.CTkFont(size=12, weight="bold"), text_color="#94a3b8").pack(anchor="w", pady=(10, 3))
        type_names = [row["name"] for row in self.investor_types]
        current_type = next((row["name"] for row in self.investor_types if investor and row["id"] == investor.get("type_id")), type_names[0] if type_names else "")
        type_var = ctk.StringVar(value=current_type)
        ctk.CTkOptionMenu(form, values=type_names or [""], variable=type_var, fg_color="#1e293b", button_color="#334155", height=40, corner_radius=10, font=ctk.CTkFont(size=13)).pack(fill="x")

        ctk.CTkLabel(form, text="Status", font=ctk.CTkFont(size=12, weight="bold"), text_color="#94a3b8").pack(anchor="w", pady=(10, 3))
        status_var = ctk.StringVar(value="Active" if not investor or investor.get("is_active") else "Inactive")
        ctk.CTkOptionMenu(form, values=["Active", "Inactive"], variable=status_var, fg_color="#1e293b", button_color="#334155", height=40, corner_radius=10, font=ctk.CTkFont(size=13)).pack(fill="x")

        ctk.CTkLabel(form, text="Address", font=ctk.CTkFont(size=12, weight="bold"), text_color="#94a3b8").pack(anchor="w", pady=(10, 3))
        address_box = ctk.CTkTextbox(form, height=100, fg_color="#1e293b", border_color="#334155", border_width=1, corner_radius=10, wrap="word")
        address_box.insert("1.0", str(investor.get("address", "") or "") if investor else "")
        address_box.pack(fill="x")

        ctk.CTkLabel(form, text="Notes / Comment", font=ctk.CTkFont(size=12, weight="bold"), text_color="#94a3b8").pack(anchor="w", pady=(10, 3))
        notes_box = ctk.CTkTextbox(form, height=110, fg_color="#1e293b", border_color="#334155", border_width=1, corner_radius=10, wrap="word")
        notes_box.insert("1.0", str(investor.get("notes", "") or "") if investor else "")
        notes_box.pack(fill="x")

        def save():
            name = fields["name"].get().strip()
            if not name:
                messagebox.showwarning("Validation", "Name is required")
                return
            type_id = next((row["id"] for row in self.investor_types if row["name"] == type_var.get()), None)
            active = 1 if status_var.get() == "Active" else 0
            payload = (
                name,
                fields["email"].get().strip() or None,
                fields["phone"].get().strip() or None,
                address_box.get("1.0", "end").strip() or None,
                type_id,
                fields["company"].get().strip() or None,
                fields["national_id"].get().strip() or None,
                fields["bank_name"].get().strip() or None,
                fields["bank_account"].get().strip() or None,
                active,
                notes_box.get("1.0", "end").strip() or None,
            )
            try:
                if investor:
                    execute_query(
                        "UPDATE investors SET name=%s, email=%s, phone=%s, address=%s, type_id=%s, company=%s, national_id=%s, bank_name=%s, bank_account=%s, is_active=%s, notes=%s, updated_at=NOW() WHERE id=%s",
                        payload + (investor["id"],),
                        fetch=False,
                    )
                else:
                    execute_query(
                        "INSERT INTO investors (name, email, phone, address, type_id, company, national_id, bank_name, bank_account, is_active, notes, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())",
                        payload,
                        fetch=False,
                    )
            except Exception as exc:
                messagebox.showerror("Error", str(exc))
                return
            dialog.destroy()
            self.load_data()

        footer = ctk.CTkFrame(dialog, fg_color="transparent")
        footer.pack(fill="x", padx=30, pady=(10, 20))
        ctk.CTkButton(footer, text="Cancel", fg_color="#1e293b", hover_color="#334155", height=40, corner_radius=10, border_width=1, border_color="#334155", command=dialog.destroy).pack(side="left")
        ctk.CTkButton(footer, text="Save", fg_color="#3b82f6", hover_color="#2563eb", height=40, corner_radius=10, font=ctk.CTkFont(weight="bold"), command=save).pack(side="right")

    def delete_investor(self, investor_id):
        if not messagebox.askyesno(
            "Confirm",
            "Delete this investor and related records?\n\nThey will be moved to Recycle Bin.",
        ):
            return
        try:
            investor_id = int(investor_id)

            for table, column in [
                ("investments", "investor_id"),
                ("payment_schedules", "investor_id"),
                ("cash_transactions", "investor_id"),
            ]:
                try:
                    rows = execute_query(f"SELECT id FROM `{table}` WHERE `{column}`=%s", (investor_id,))
                    ids = [int(r["id"]) for r in (rows or []) if r.get("id") is not None]
                    if ids:
                        recycle_and_delete_many(
                            table,
                            ids,
                            deleted_by=self.user.get("id"),
                            reason=f"Deleted with investor {investor_id}",
                        )
                except Exception:
                    pass

            recycle_and_delete(
                "investors",
                investor_id,
                deleted_by=self.user.get("id"),
                reason="Deleted investor",
            )
            self.load_data()
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
