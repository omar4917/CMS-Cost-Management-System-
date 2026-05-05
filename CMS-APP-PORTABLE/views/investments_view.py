"""
Transaction entry view for the desktop app.
Supports investments plus manual buy, sell, and cost-style cash movements.
"""

from datetime import date, datetime
from tkinter import messagebox

import customtkinter as ctk

from core.database import ensure_cash_transactions_table, execute_query
from core.desktop_utils import as_float, format_date, parse_date
from core.recycle_bin import recycle_and_delete
from core.transaction_utils import editable_meta_for_row, transaction_code, transaction_detail_rows, transaction_source_label


TYPE_META = {
    "Investment": ("investment", "inflow"),
    "Sale": ("sale", "inflow"),
    "Buy": ("buy", "outflow"),
    "Cost": ("cost", "outflow"),
    "Expense": ("expense", "outflow"),
    "Refund In": ("refund_in", "inflow"),
    "Refund Out": ("refund_out", "outflow"),
    "Other Inflow": ("other_inflow", "inflow"),
    "Other Outflow": ("other_outflow", "outflow"),
}


class InvestmentsView(ctk.CTkFrame):
    def __init__(self, parent, user):
        super().__init__(parent, fg_color="transparent")
        self.user = user
        self.rows = []
        try:
            ensure_cash_transactions_table()
        except Exception:
            pass
        self.build_ui()
        self.load_data()

    def build_ui(self):
        hero = ctk.CTkFrame(
            self,
            fg_color="#0d1630",
            corner_radius=22,
            border_width=1,
            border_color="#233154",
        )
        hero.pack(fill="x", pady=(0, 14))

        header = ctk.CTkFrame(hero, fg_color="transparent")
        header.pack(fill="x", padx=22, pady=(18, 12))

        title_col = ctk.CTkFrame(header, fg_color="transparent")
        title_col.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(
            title_col,
            text="Transactions Studio",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="#f8fafc",
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_col,
            text="Record investments, sales, buys, and operating cash movements from one desk.",
            font=ctk.CTkFont(size=13),
            text_color="#8ea3c7",
        ).pack(anchor="w", pady=(4, 0))

        ctk.CTkButton(
            header,
            text="+ Record Transaction",
            fg_color="#19c37d",
            hover_color="#14a568",
            corner_radius=12,
            height=42,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.open_add,
        ).pack(side="right")

        self.summary_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.summary_frame.pack(fill="x", pady=(0, 12))
        for index in range(4):
            self.summary_frame.grid_columnconfigure(index, weight=1)

        self.summary_cards = {}
        for column, key, label, color in [
            (0, "inflow", "Money In", "#27d3a2"),
            (1, "outflow", "Money Out", "#ff7a90"),
            (2, "net", "Net Flow", "#4f8cff"),
            (3, "records", "Records", "#f6c85f"),
        ]:
            card = ctk.CTkFrame(
                self.summary_frame,
                fg_color="#111d39",
                corner_radius=16,
                border_width=1,
                border_color="#233154",
                height=86,
            )
            card.grid(row=0, column=column, padx=5, pady=4, sticky="nsew")
            card.pack_propagate(False)
            ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=11), text_color="#7184aa").pack(
                anchor="w", padx=16, pady=(14, 0)
            )
            value = ctk.CTkLabel(card, text="-", font=ctk.CTkFont(size=22, weight="bold"), text_color=color)
            value.pack(anchor="w", padx=16, pady=(6, 0))
            self.summary_cards[key] = value

        filters = ctk.CTkFrame(
            self,
            fg_color="#0d1630",
            corner_radius=18,
            border_width=1,
            border_color="#1f2a45",
        )
        filters.pack(fill="x", pady=(0, 12))

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_args: self.render_rows())
        ctk.CTkEntry(
            filters,
            textvariable=self.search_var,
            placeholder_text="Search party, project, reference, or notes...",
            height=40,
            corner_radius=10,
            fg_color="#101b35",
            border_color="#233154",
            width=320,
        ).pack(side="left", padx=10, pady=10)

        self.direction_var = ctk.StringVar(value="All Entries")
        ctk.CTkOptionMenu(
            filters,
            variable=self.direction_var,
            values=["All Entries", "Money In", "Money Out"],
            command=lambda _value: self.render_rows(),
            fg_color="#152140",
            button_color="#233154",
            button_hover_color="#31446b",
            dropdown_fg_color="#111d39",
            corner_radius=10,
            height=40,
            width=150,
        ).pack(side="left", padx=(0, 10), pady=10)

        self.type_var = ctk.StringVar(value="All Types")
        self.type_menu = ctk.CTkOptionMenu(
            filters,
            variable=self.type_var,
            values=["All Types"] + list(TYPE_META.keys()),
            command=lambda _value: self.render_rows(),
            fg_color="#152140",
            button_color="#233154",
            button_hover_color="#31446b",
            dropdown_fg_color="#111d39",
            corner_radius=10,
            height=40,
            width=160,
        )
        self.type_menu.pack(side="left", pady=10)

        self.table_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="#0d1630",
            corner_radius=18,
            border_width=1,
            border_color="#1f2a45",
        )
        self.table_frame.pack(fill="both", expand=True)

    def load_data(self):
        try:
            self.rows = self._fetch_rows()
        except Exception as exc:
            for widget in self.table_frame.winfo_children():
                widget.destroy()
            ctk.CTkLabel(self.table_frame, text=f"Error loading transactions: {exc}", text_color="#ef4444").pack(pady=24)
            return
        self.render_rows()

    def render_rows(self):
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        rows = list(self.rows)
        search = self.search_var.get().strip().lower()
        if search:
            rows = [
                row
                for row in rows
                if search in " ".join(
                    str(row.get(key, "") or "")
                    for key in ("kind", "party_name", "project_name", "reference_no", "notes")
                ).lower()
            ]

        if self.direction_var.get() == "Money In":
            rows = [row for row in rows if row.get("direction") == "inflow"]
        elif self.direction_var.get() == "Money Out":
            rows = [row for row in rows if row.get("direction") == "outflow"]

        if self.type_var.get() != "All Types":
            rows = [row for row in rows if row.get("kind") == self.type_var.get()]

        rows.sort(key=lambda row: parse_date(row.get("tx_date")) or datetime.min, reverse=True)

        total_in = sum(as_float(row.get("amount")) for row in rows if row.get("direction") == "inflow")
        total_out = sum(as_float(row.get("amount")) for row in rows if row.get("direction") == "outflow")
        net = total_in - total_out
        self.summary_cards["inflow"].configure(text=f"BDT {total_in:,.0f}")
        self.summary_cards["outflow"].configure(text=f"BDT {total_out:,.0f}")
        self.summary_cards["net"].configure(text=f"BDT {net:,.0f}")
        self.summary_cards["records"].configure(text=str(len(rows)))

        if not rows:
            empty = ctk.CTkFrame(self.table_frame, fg_color="transparent")
            empty.pack(expand=True, pady=80)
            ctk.CTkLabel(empty, text="No transactions yet", font=ctk.CTkFont(size=20, weight="bold"), text_color="#d8e4ff").pack()
            ctk.CTkLabel(
                empty,
                text="Use Record Transaction to add investments, sales, buys, or cost flows.",
                font=ctk.CTkFont(size=12),
                text_color="#6e84ac",
            ).pack(pady=(6, 0))
            return

        for row in rows:
            card = ctk.CTkFrame(
                self.table_frame,
                fg_color="#111d39",
                corner_radius=16,
                border_width=1,
                border_color="#223356",
            )
            card.pack(fill="x", padx=8, pady=6)

            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=16, pady=(14, 6))

            title_wrap = ctk.CTkFrame(top, fg_color="transparent")
            title_wrap.pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(
                title_wrap,
                text=transaction_code(row),
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="#8aa0c8",
            ).pack(anchor="w")
            ctk.CTkLabel(
                title_wrap,
                text=row["kind"],
                font=ctk.CTkFont(size=15, weight="bold"),
                text_color=self._type_color(row["kind"]),
            ).pack(anchor="w", pady=(2, 0))

            action_wrap = ctk.CTkFrame(top, fg_color="transparent")
            action_wrap.pack(side="right")
            amount_color = "#27d3a2" if row.get("direction") == "inflow" else "#ff7a90"
            amount_prefix = "+" if row.get("direction") == "inflow" else "-"
            ctk.CTkLabel(
                action_wrap,
                text=f"{amount_prefix} BDT {as_float(row.get('amount')):,.0f}",
                font=ctk.CTkFont(size=15, weight="bold"),
                text_color=amount_color,
            ).pack(side="left", padx=(0, 12))
            ctk.CTkButton(
                action_wrap,
                text="Delete",
                width=70,
                height=30,
                corner_radius=8,
                fg_color="#1a2642",
                hover_color="#7f1d1d",
                text_color="#ff9aa2",
                command=lambda item=row: self.delete_row(item),
            ).pack(side="left")

            meta = [
                f"Date: {format_date(row.get('tx_date'))}",
                f"Project: {row.get('project_name') or 'Unassigned'}",
                f"Party: {row.get('party_name') or 'N/A'}",
                f"Source: {transaction_source_label(row)}",
            ]
            if row.get("reference_no"):
                meta.append(f"Reference: {row['reference_no']}")
            if row.get("payment_method"):
                meta.append(f"Method: {str(row['payment_method']).replace('_', ' ').title()}")
            ctk.CTkLabel(
                card,
                text="  |  ".join(meta),
                font=ctk.CTkFont(size=12),
                text_color="#8aa0c8",
                wraplength=980,
                justify="left",
            ).pack(anchor="w", padx=16, pady=(0, 8))

            if row.get("notes"):
                ctk.CTkLabel(
                    card,
                    text=row["notes"],
                    font=ctk.CTkFont(size=12),
                    text_color="#d7e3ff",
                    wraplength=980,
                    justify="left",
                ).pack(anchor="w", padx=16, pady=(0, 14))
            else:
                ctk.CTkFrame(card, fg_color="transparent", height=8).pack()

            self._bind_click(card, lambda _event, item=row: self.open_transaction_detail(item))

    def _fetch_rows(self):
        rows = []

        investment_rows = execute_query(
            """
            SELECT inv.id, inv.amount, inv.date, inv.reference_no, inv.payment_method, inv.notes,
                   i.name AS investor_name, p.name AS project_name
            FROM investments inv
            LEFT JOIN investors i ON inv.investor_id = i.id
            LEFT JOIN projects p ON inv.project_id = p.id
            ORDER BY inv.date DESC, inv.id DESC
            """
        )
        for row in investment_rows:
            rows.append(
                {
                    "kind": "Investment",
                    "entry_type": "investment",
                    "direction": "inflow",
                    "amount": row.get("amount"),
                    "tx_date": row.get("date"),
                    "project_name": row.get("project_name"),
                    "party_name": row.get("investor_name"),
                    "reference_no": row.get("reference_no"),
                    "payment_method": row.get("payment_method"),
                    "notes": row.get("notes"),
                    "source_table": "investments",
                    "source_name": "investments",
                    "source_id": row.get("id"),
                }
            )

        try:
            manual_rows = execute_query(
                """
                SELECT ct.id, ct.entry_type, ct.direction, ct.amount, ct.tx_date, ct.counterparty,
                       ct.reference_no, ct.payment_method, ct.notes,
                       p.name AS project_name, i.name AS investor_name, c.name AS contractor_name
                FROM cash_transactions ct
                LEFT JOIN projects p ON ct.project_id = p.id
                LEFT JOIN investors i ON ct.investor_id = i.id
                LEFT JOIN contractors c ON ct.contractor_id = c.id
                ORDER BY ct.tx_date DESC, ct.id DESC
                """
            )
        except Exception:
            manual_rows = []

        for row in manual_rows:
            rows.append(
                {
                    "kind": self._kind_from_entry(row.get("entry_type")),
                    "entry_type": row.get("entry_type"),
                    "direction": row.get("direction") or "outflow",
                    "amount": row.get("amount"),
                    "tx_date": row.get("tx_date"),
                    "project_name": row.get("project_name"),
                    "party_name": row.get("counterparty") or row.get("investor_name") or row.get("contractor_name"),
                    "reference_no": row.get("reference_no"),
                    "payment_method": row.get("payment_method"),
                    "notes": row.get("notes"),
                    "source_table": "cash_transactions",
                    "source_name": row.get("source_table") or "manual",
                    "source_id": row.get("id"),
                }
            )

        return rows

    def open_add(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Record Transaction")
        dialog.geometry("620x690")
        dialog.configure(fg_color="#0f172a")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        ctk.CTkLabel(
            dialog,
            text="Record Transaction",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#f8fafc",
        ).pack(pady=(20, 12))

        form = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=30)

        try:
            investors = execute_query("SELECT id, name FROM investors WHERE is_active = 1 ORDER BY name")
        except Exception:
            investors = []
        try:
            projects = execute_query("SELECT id, name FROM projects ORDER BY name")
        except Exception:
            projects = []

        investor_map = {f"{row['name']} (#{row['id']})": row["id"] for row in investors}
        project_map = {f"{row['name']} (#{row['id']})": row["id"] for row in projects}

        ctk.CTkLabel(form, text="Transaction Type", font=ctk.CTkFont(size=12, weight="bold"), text_color="#9bb0d5").pack(
            anchor="w", pady=(8, 4)
        )
        type_var = ctk.StringVar(value="Investment")
        ctk.CTkOptionMenu(
            form,
            values=list(TYPE_META.keys()),
            variable=type_var,
            fg_color="#1e293b",
            button_color="#334155",
            dropdown_fg_color="#111d39",
            height=40,
            corner_radius=10,
        ).pack(fill="x")

        direction_hint = ctk.CTkLabel(form, text="", text_color="#7dd3fc", font=ctk.CTkFont(size=11, weight="bold"))
        direction_hint.pack(anchor="w", pady=(6, 0))

        ctk.CTkLabel(form, text="Project", font=ctk.CTkFont(size=12, weight="bold"), text_color="#9bb0d5").pack(
            anchor="w", pady=(12, 4)
        )
        project_choices = ["None"] + list(project_map.keys())
        project_var = ctk.StringVar(value=project_choices[0] if project_choices else "None")
        ctk.CTkOptionMenu(
            form,
            values=project_choices or ["None"],
            variable=project_var,
            fg_color="#1e293b",
            button_color="#334155",
            dropdown_fg_color="#111d39",
            height=40,
            corner_radius=10,
        ).pack(fill="x")

        investor_wrap = ctk.CTkFrame(form, fg_color="transparent")
        investor_wrap.pack(fill="x")
        ctk.CTkLabel(
            investor_wrap,
            text="Investor",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#9bb0d5",
        ).pack(anchor="w", pady=(12, 4))
        investor_choices = ["None"] + list(investor_map.keys())
        investor_var = ctk.StringVar(value=investor_choices[0] if investor_choices else "None")
        investor_menu = ctk.CTkOptionMenu(
            investor_wrap,
            values=investor_choices or ["None"],
            variable=investor_var,
            fg_color="#1e293b",
            button_color="#334155",
            dropdown_fg_color="#111d39",
            height=40,
            corner_radius=10,
        )
        investor_menu.pack(fill="x")

        ctk.CTkLabel(form, text="Counterparty", font=ctk.CTkFont(size=12, weight="bold"), text_color="#9bb0d5").pack(
            anchor="w", pady=(12, 4)
        )
        counterparty_entry = ctk.CTkEntry(
            form,
            height=40,
            corner_radius=10,
            fg_color="#1e293b",
            border_color="#334155",
            placeholder_text="Buyer, seller, supplier, office, or other counterparty",
        )
        counterparty_entry.pack(fill="x")

        field_specs = [
            ("Amount (BDT)", "amount", ""),
            ("Transaction Date", "tx_date", date.today().isoformat()),
            ("Payment Method", "payment_method", "bank_transfer"),
            ("Reference / Voucher No", "reference_no", ""),
        ]
        entries = {}
        for label, key, default in field_specs:
            ctk.CTkLabel(form, text=label, font=ctk.CTkFont(size=12, weight="bold"), text_color="#9bb0d5").pack(
                anchor="w", pady=(12, 4)
            )
            if key == "payment_method":
                var = ctk.StringVar(value=default)
                ctk.CTkOptionMenu(
                    form,
                    values=["bank_transfer", "cash", "cheque", "mobile_banking"],
                    variable=var,
                    fg_color="#1e293b",
                    button_color="#334155",
                    dropdown_fg_color="#111d39",
                    height=40,
                    corner_radius=10,
                ).pack(fill="x")
                entries[key] = var
            else:
                entry = ctk.CTkEntry(
                    form,
                    height=40,
                    corner_radius=10,
                    fg_color="#1e293b",
                    border_color="#334155",
                )
                if default:
                    entry.insert(0, default)
                entry.pack(fill="x")
                entries[key] = entry

        ctk.CTkLabel(form, text="Note / Comment", font=ctk.CTkFont(size=12, weight="bold"), text_color="#9bb0d5").pack(
            anchor="w", pady=(12, 4)
        )
        notes_box = ctk.CTkTextbox(
            form,
            height=110,
            corner_radius=10,
            fg_color="#1e293b",
            border_color="#334155",
            border_width=1,
        )
        notes_box.pack(fill="x")

        def refresh_mode(*_args):
            entry_type, direction = TYPE_META[type_var.get()]
            direction_hint.configure(text=f"Flow Direction: {direction.title()}")
            if entry_type == "investment":
                investor_wrap.pack(fill="x")
                counterparty_entry.configure(state="disabled")
                counterparty_entry.delete(0, "end")
            else:
                investor_wrap.pack_forget()
                counterparty_entry.configure(state="normal")

        type_var.trace_add("write", refresh_mode)
        refresh_mode()

        def save():
            entry_type, direction = TYPE_META[type_var.get()]
            project_id = project_map.get(project_var.get()) if project_var.get() != "None" else None
            investor_id = investor_map.get(investor_var.get()) if investor_var.get() != "None" else None
            counterparty = counterparty_entry.get().strip()
            amount_text = entries["amount"].get().strip()
            tx_date = entries["tx_date"].get().strip()
            payment_method = entries["payment_method"].get().strip()
            reference_no = entries["reference_no"].get().strip()
            notes = notes_box.get("1.0", "end").strip()

            if not amount_text:
                messagebox.showwarning("Validation", "Amount is required")
                return

            try:
                amount = float(amount_text)
            except ValueError:
                messagebox.showwarning("Validation", "Amount must be numeric")
                return

            if not tx_date:
                messagebox.showwarning("Validation", "Transaction date is required")
                return

            try:
                if entry_type == "investment":
                    if not investor_id:
                        messagebox.showwarning("Validation", "Choose an investor for investment entries")
                        return
                    execute_query(
                        "INSERT INTO investments (investor_id, project_id, amount, currency, date, payment_method, reference_no, status, notes, created_by, created_at, updated_at) "
                        "VALUES (%s, %s, %s, 'BDT', %s, %s, %s, 'confirmed', %s, %s, NOW(), NOW())",
                        (investor_id, project_id, amount, tx_date, payment_method, reference_no, notes, self.user.get("id")),
                        fetch=False,
                    )
                else:
                    execute_query(
                        "INSERT INTO cash_transactions (project_id, investor_id, contractor_id, entry_type, direction, amount, currency, tx_date, counterparty, reference_no, payment_method, status, source_table, notes, created_by, created_at, updated_at) "
                        "VALUES (%s, %s, NULL, %s, %s, %s, 'BDT', %s, %s, %s, %s, 'confirmed', 'manual', %s, %s, NOW(), NOW())",
                        (
                            project_id,
                            investor_id,
                            entry_type,
                            direction,
                            amount,
                            tx_date,
                            counterparty or None,
                            reference_no or None,
                            payment_method or None,
                            notes or None,
                            self.user.get("id"),
                        ),
                        fetch=False,
                    )
            except Exception as exc:
                messagebox.showerror("Error", str(exc))
                return

            dialog.destroy()
            self.load_data()

        footer = ctk.CTkFrame(dialog, fg_color="transparent")
        footer.pack(fill="x", padx=30, pady=(10, 20))
        ctk.CTkButton(
            footer,
            text="Cancel",
            fg_color="#1e293b",
            hover_color="#334155",
            height=40,
            corner_radius=10,
            command=dialog.destroy,
        ).pack(side="left")
        ctk.CTkButton(
            footer,
            text="Save",
            fg_color="#19c37d",
            hover_color="#14a568",
            height=40,
            corner_radius=10,
            font=ctk.CTkFont(weight="bold"),
            command=save,
        ).pack(side="right")

    def delete_row(self, row):
        if not messagebox.askyesno("Confirm", "Delete this transaction record? It will be moved to Recycle Bin."):
            return

        try:
            if row.get("source_table") == "investments":
                recycle_and_delete(
                    "investments",
                    int(row.get("source_id")),
                    deleted_by=self.user.get("id"),
                    reason="Deleted from Investments view",
                )
            elif row.get("source_table") == "cash_transactions":
                recycle_and_delete(
                    "cash_transactions",
                    int(row.get("source_id")),
                    deleted_by=self.user.get("id"),
                    reason="Deleted from Investments view",
                )
            else:
                messagebox.showinfo("Not supported", "This transaction is generated from another module.")
                return
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
            return

        self.load_data()

    def open_transaction_detail(self, row):
        dialog = ctk.CTkToplevel(self)
        dialog.title(transaction_code(row))
        dialog.geometry("640x700")
        dialog.configure(fg_color="#0f172a")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        ctk.CTkLabel(
            dialog,
            text=transaction_code(row),
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#f8fafc",
        ).pack(anchor="w", padx=28, pady=(24, 4))
        ctk.CTkLabel(
            dialog,
            text=f"{row.get('kind') or 'Transaction'}  |  {transaction_source_label(row)}",
            font=ctk.CTkFont(size=12),
            text_color="#8aa0c8",
        ).pack(anchor="w", padx=28)

        body = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=(16, 10))

        info = ctk.CTkFrame(body, fg_color="#111827", corner_radius=16, border_width=1, border_color="#223356")
        info.pack(fill="x")
        for label, value in transaction_detail_rows(row):
            line = ctk.CTkFrame(info, fg_color="transparent")
            line.pack(fill="x", padx=16, pady=8)
            ctk.CTkLabel(
                line,
                text=label,
                width=140,
                anchor="w",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#9bb0d5",
            ).pack(side="left")
            ctk.CTkLabel(
                line,
                text=value,
                font=ctk.CTkFont(size=12),
                text_color="#f8fafc",
                wraplength=380,
                justify="left",
            ).pack(side="left", fill="x", expand=True)

        edit_meta = editable_meta_for_row(row) or {}

        ctk.CTkLabel(
            body,
            text="Reference",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#9bb0d5",
        ).pack(anchor="w", pady=(16, 4))
        if edit_meta.get("reference"):
            reference_entry = ctk.CTkEntry(
                body,
                height=40,
                corner_radius=10,
                fg_color="#111827",
                border_color="#223356",
            )
            reference_entry.insert(0, str(row.get("reference_no") or ""))
            reference_entry.pack(fill="x")
        else:
            reference_entry = None
            ctk.CTkLabel(
                body,
                text=row.get("reference_no") or "No reference saved",
                font=ctk.CTkFont(size=12),
                text_color="#d7e3ff",
            ).pack(anchor="w")

        ctk.CTkLabel(
            body,
            text="Note / Comment",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#9bb0d5",
        ).pack(anchor="w", pady=(16, 4))
        notes_box = ctk.CTkTextbox(
            body,
            height=180,
            corner_radius=12,
            fg_color="#111827",
            border_color="#223356",
            border_width=1,
            wrap="word",
        )
        notes_box.insert("1.0", str(row.get("notes") or ""))
        notes_box.pack(fill="x")
        if not edit_meta.get("notes"):
            notes_box.configure(state="disabled")

        footer = ctk.CTkFrame(dialog, fg_color="transparent")
        footer.pack(fill="x", padx=24, pady=(0, 20))
        ctk.CTkButton(
            footer,
            text="Close",
            fg_color="#1e293b",
            hover_color="#334155",
            height=38,
            corner_radius=10,
            command=dialog.destroy,
        ).pack(side="left")

        if edit_meta:
            ctk.CTkButton(
                footer,
                text="Save Changes",
                fg_color="#19c37d",
                hover_color="#14a568",
                height=38,
                corner_radius=10,
                command=lambda: self._save_transaction_meta(row, edit_meta, reference_entry, notes_box, dialog),
            ).pack(side="right")

    def _save_transaction_meta(self, row, edit_meta, reference_entry, notes_box, dialog):
        updates = []
        params = []

        reference_col = edit_meta.get("reference")
        if reference_col and reference_entry is not None:
            updates.append(f"{reference_col}=%s")
            params.append(reference_entry.get().strip() or None)

        notes_col = edit_meta.get("notes")
        if notes_col:
            updates.append(f"{notes_col}=%s")
            params.append(notes_box.get("1.0", "end").strip() or None)

        if not updates:
            dialog.destroy()
            return

        try:
            execute_query(
                f"UPDATE {row['source_table']} SET {', '.join(updates)}, updated_at=NOW() WHERE id=%s",
                tuple(params + [row.get("source_id")]),
                fetch=False,
            )
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
            return

        dialog.destroy()
        self.load_data()

    def _bind_click(self, widget, callback):
        if isinstance(widget, ctk.CTkButton):
            return
        widget.bind("<Button-1>", callback)
        for child in widget.winfo_children():
            self._bind_click(child, callback)

    def _kind_from_entry(self, entry_type):
        entry_type = str(entry_type or "").strip().lower()
        for label, (slug, _direction) in TYPE_META.items():
            if slug == entry_type:
                return label
        return "Other Outflow"

    def _type_color(self, kind):
        return {
            "Investment": "#27d3a2",
            "Sale": "#4ade80",
            "Buy": "#f59e0b",
            "Cost": "#fb7185",
            "Expense": "#ff7a90",
            "Refund In": "#7dd3fc",
            "Refund Out": "#f97316",
            "Other Inflow": "#4f8cff",
            "Other Outflow": "#c084fc",
        }.get(kind, "#d8e4ff")
