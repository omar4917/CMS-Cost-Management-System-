"""
Ledger view for the desktop app.
Combines investments, schedules, costs, contractor payouts, and manual cash transactions.
"""

from datetime import datetime

import customtkinter as ctk

from core.database import ensure_cash_transactions_table, execute_query
from core.desktop_utils import as_float, format_date, parse_date, pick_column
from core.transaction_utils import editable_meta_for_row, transaction_code, transaction_detail_rows, transaction_source_label


class TransactionsView(ctk.CTkFrame):
    def __init__(self, parent, user):
        super().__init__(parent, fg_color="transparent")
        self.user = user
        self.rows = []
        self.contractor_payment_date_col = pick_column("contractor_payments", "date", "payment_date", fallback="date")
        try:
            ensure_cash_transactions_table()
        except Exception:
            pass
        self.build_ui()
        self.load_transactions()

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
        header.pack(fill="x", padx=22, pady=(18, 8))

        title_col = ctk.CTkFrame(header, fg_color="transparent")
        title_col.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(
            title_col,
            text="Live Ledger",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="#f8fafc",
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_col,
            text="Watch capital in, capital out, and manual buy or sell movements in one stream.",
            font=ctk.CTkFont(size=13),
            text_color="#8ea3c7",
        ).pack(anchor="w", pady=(4, 0))

        filter_wrap = ctk.CTkFrame(hero, fg_color="transparent")
        filter_wrap.pack(fill="x", padx=22, pady=(4, 18))

        self.direction_var = ctk.StringVar(value="All Entries")
        ctk.CTkOptionMenu(
            filter_wrap,
            variable=self.direction_var,
            values=["All Entries", "Money In", "Money Out"],
            command=lambda _value: self.render_rows(),
            fg_color="#152140",
            button_color="#233154",
            button_hover_color="#31446b",
            dropdown_fg_color="#111d39",
            corner_radius=10,
            height=40,
            width=180,
        ).pack(side="left")

        self.type_var = ctk.StringVar(value="All Types")
        self.type_menu = ctk.CTkOptionMenu(
            filter_wrap,
            variable=self.type_var,
            values=["All Types"],
            command=lambda _value: self.render_rows(),
            fg_color="#152140",
            button_color="#233154",
            button_hover_color="#31446b",
            dropdown_fg_color="#111d39",
            corner_radius=10,
            height=40,
            width=180,
        )
        self.type_menu.pack(side="left", padx=(10, 0))

        self.metric_labels = {}
        for key, label, color in [
            ("inflow", "Money In", "#27d3a2"),
            ("outflow", "Money Out", "#ff7a90"),
            ("balance", "Net", "#4f8cff"),
            ("records", "Records", "#f6c85f"),
        ]:
            card = ctk.CTkFrame(
                filter_wrap,
                fg_color="#111d39",
                corner_radius=14,
                border_width=1,
                border_color="#233154",
                height=72,
            )
            card.pack(side="left", padx=(12, 0), fill="x", expand=True)
            card.pack_propagate(False)
            ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=11), text_color="#7789ac").pack(
                anchor="w", padx=14, pady=(12, 0)
            )
            value_label = ctk.CTkLabel(
                card,
                text="-",
                font=ctk.CTkFont(size=20, weight="bold"),
                text_color=color,
            )
            value_label.pack(anchor="w", padx=14, pady=(4, 0))
            self.metric_labels[key] = value_label

        self.table_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="#0d1630",
            corner_radius=18,
            border_width=1,
            border_color="#1f2a45",
        )
        self.table_frame.pack(fill="both", expand=True)

    def load_transactions(self):
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        try:
            self.rows = self._fetch_rows()
        except Exception as exc:
            ctk.CTkLabel(self.table_frame, text=f"Error loading ledger: {exc}", text_color="#ef4444").pack(pady=24)
            return

        type_values = ["All Types"] + sorted({row["kind"] for row in self.rows})
        if self.type_var.get() not in type_values:
            self.type_var.set("All Types")
        self.type_menu.configure(values=type_values)
        self.render_rows()

    def render_rows(self):
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        rows = list(self.rows)
        selected_direction = self.direction_var.get()
        selected_type = self.type_var.get()

        if selected_direction == "Money In":
            rows = [row for row in rows if row.get("direction") == "inflow"]
        elif selected_direction == "Money Out":
            rows = [row for row in rows if row.get("direction") == "outflow"]

        if selected_type != "All Types":
            rows = [row for row in rows if row.get("kind") == selected_type]

        rows.sort(key=lambda row: parse_date(row.get("tx_date")) or datetime.min, reverse=True)

        total_in = sum(as_float(row.get("amount")) for row in rows if row.get("direction") == "inflow")
        total_out = sum(as_float(row.get("amount")) for row in rows if row.get("direction") == "outflow")
        balance = total_in - total_out

        self.metric_labels["inflow"].configure(text=f"BDT {total_in:,.0f}")
        self.metric_labels["outflow"].configure(text=f"BDT {total_out:,.0f}")
        self.metric_labels["balance"].configure(text=f"BDT {balance:,.0f}")
        self.metric_labels["records"].configure(text=str(len(rows)))

        if not rows:
            empty = ctk.CTkFrame(self.table_frame, fg_color="transparent")
            empty.pack(expand=True, pady=80)
            ctk.CTkLabel(empty, text="No ledger activity", font=ctk.CTkFont(size=20, weight="bold"), text_color="#d8e4ff").pack()
            ctk.CTkLabel(
                empty,
                text="Record investments, buys, sales, costs, or contractor payouts to populate the ledger.",
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
            top.pack(fill="x", padx=16, pady=(14, 4))

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

            amount = as_float(row.get("amount"))
            amount_color = "#27d3a2" if row.get("direction") == "inflow" else "#ff7a90"
            amount_prefix = "+" if row.get("direction") == "inflow" else "-"
            ctk.CTkLabel(
                top,
                text=f"{amount_prefix} BDT {amount:,.0f}",
                font=ctk.CTkFont(size=15, weight="bold"),
                text_color=amount_color,
            ).pack(side="right")

            meta = ctk.CTkLabel(
                card,
                text=self._describe_row(row),
                font=ctk.CTkFont(size=12),
                text_color="#8aa0c8",
                wraplength=980,
                justify="left",
            )
            meta.pack(anchor="w", padx=16, pady=(0, 8))

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
                ctk.CTkFrame(card, fg_color="transparent", height=6).pack()

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
            WHERE inv.status = 'confirmed'
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

        schedule_rows = execute_query(
            """
            SELECT ps.id, ps.amount, ps.paid_date, ps.notes,
                   i.name AS investor_name, p.name AS project_name
            FROM payment_schedules ps
            LEFT JOIN investors i ON ps.investor_id = i.id
            LEFT JOIN projects p ON ps.project_id = p.id
            WHERE ps.status = 'paid' AND ps.paid_date IS NOT NULL
            ORDER BY ps.paid_date DESC, ps.id DESC
            """
        )
        for row in schedule_rows:
            rows.append(
                {
                    "kind": "Schedule Payment",
                    "entry_type": "schedule_payment",
                    "direction": "inflow",
                    "amount": row.get("amount"),
                    "tx_date": row.get("paid_date"),
                    "project_name": row.get("project_name"),
                    "party_name": row.get("investor_name"),
                    "reference_no": None,
                    "payment_method": None,
                    "notes": row.get("notes"),
                    "source_table": "payment_schedules",
                    "source_name": "payment_schedules",
                    "source_id": row.get("id"),
                }
            )

        cost_rows = execute_query(
            """
            SELECT ci.id,
                   CASE
                       WHEN ci.cost_amount IS NOT NULL AND ci.cost_amount <> 0 THEN ci.cost_amount
                       WHEN ci.actual_amount IS NOT NULL AND ci.actual_amount <> 0 THEN ci.actual_amount
                       WHEN ci.estimated_amount IS NOT NULL AND ci.estimated_amount <> 0 THEN ci.estimated_amount
                       ELSE 0
                   END AS actual_amount,
                   COALESCE(ci.cost_date, ci.date, ci.created_at) AS tx_date,
                   COALESCE(ci.cost_detail, ci.description, ci.name) AS name,
                   ci.invoice_no AS invoice_no,
                   COALESCE(ci.pay_to, ci.vendor) AS vendor,
                   COALESCE(ci.remarks, ci.notes) AS notes,
                   COALESCE(p.name, ci.cost_head_project) AS project_name
            FROM cost_items ci
            LEFT JOIN projects p ON ci.project_id = p.id
            WHERE COALESCE(NULLIF(ci.cost_amount, 0), NULLIF(ci.actual_amount, 0), NULLIF(ci.estimated_amount, 0)) IS NOT NULL
            ORDER BY COALESCE(ci.cost_date, ci.date, ci.created_at) DESC, ci.id DESC
            """
        )
        for row in cost_rows:
            rows.append(
                {
                    "kind": "Cost Item",
                    "entry_type": "cost",
                    "direction": "outflow",
                    "amount": row.get("actual_amount"),
                    "tx_date": row.get("tx_date"),
                    "project_name": row.get("project_name"),
                    "party_name": row.get("vendor"),
                    "reference_no": row.get("invoice_no"),
                    "payment_method": None,
                    "notes": row.get("notes") or row.get("name"),
                    "source_table": "cost_items",
                    "source_name": "cost_items",
                    "source_id": row.get("id"),
                }
            )

        contractor_rows = execute_query(
            f"""
            SELECT cp.id, cp.amount, cp.{self.contractor_payment_date_col} AS tx_date, cp.invoice_no,
                   cp.description, cp.notes, c.name AS contractor_name, p.name AS project_name
            FROM contractor_payments cp
            LEFT JOIN contractors c ON cp.contractor_id = c.id
            LEFT JOIN projects p ON cp.project_id = p.id
            WHERE cp.status IN ('paid', 'approved', 'completed')
            ORDER BY cp.{self.contractor_payment_date_col} DESC, cp.id DESC
            """
        )
        for row in contractor_rows:
            rows.append(
                {
                    "kind": "Contractor Payment",
                    "entry_type": "contractor_payment",
                    "direction": "outflow",
                    "amount": row.get("amount"),
                    "tx_date": row.get("tx_date"),
                    "project_name": row.get("project_name"),
                    "party_name": row.get("contractor_name"),
                    "reference_no": row.get("invoice_no"),
                    "payment_method": None,
                    "notes": row.get("notes") or row.get("description"),
                    "source_table": "contractor_payments",
                    "source_name": "contractor_payments",
                    "source_id": row.get("id"),
                }
            )

        try:
            manual_rows = execute_query(
                """
                SELECT ct.id, ct.entry_type, ct.direction, ct.amount, ct.tx_date, ct.counterparty,
                       ct.reference_no, ct.payment_method, ct.notes, ct.source_table,
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
            party_name = row.get("counterparty") or row.get("investor_name") or row.get("contractor_name")
            rows.append(
                {
                    "kind": self._entry_kind(row.get("entry_type")),
                    "entry_type": row.get("entry_type"),
                    "direction": row.get("direction") or "outflow",
                    "amount": row.get("amount"),
                    "tx_date": row.get("tx_date"),
                    "project_name": row.get("project_name"),
                    "party_name": party_name,
                    "reference_no": row.get("reference_no"),
                    "payment_method": row.get("payment_method"),
                    "notes": row.get("notes"),
                    "source_table": "cash_transactions",
                    "source_name": row.get("source_table") or "manual",
                    "source_id": row.get("id"),
                }
            )

        return rows

    def _describe_row(self, row):
        details = [f"Date: {format_date(row.get('tx_date'))}"]

        if row.get("project_name"):
            details.append(f"Project: {row['project_name']}")
        if row.get("party_name"):
            details.append(f"Party: {row['party_name']}")
        if row.get("payment_method"):
            details.append(f"Method: {str(row['payment_method']).replace('_', ' ').title()}")
        if row.get("reference_no"):
            details.append(f"Reference: {row['reference_no']}")
        if row.get("source_table"):
            details.append(f"Source: {transaction_source_label(row)}")

        return "  |  ".join(details)

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
                fg_color="#4f8cff",
                hover_color="#3578f6",
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
            from tkinter import messagebox

            messagebox.showerror("Error", str(exc))
            return

        dialog.destroy()
        self.load_transactions()

    def _bind_click(self, widget, callback):
        if isinstance(widget, ctk.CTkButton):
            return
        widget.bind("<Button-1>", callback)
        for child in widget.winfo_children():
            self._bind_click(child, callback)

    def _entry_kind(self, entry_type):
        return {
            "investment": "Investment",
            "sale": "Sale",
            "buy": "Buy",
            "cost": "Cost",
            "expense": "Expense",
            "refund_in": "Refund In",
            "refund_out": "Refund Out",
            "other_inflow": "Other Inflow",
            "other_outflow": "Other Outflow",
        }.get(str(entry_type or "").strip().lower(), "Manual")

    def _type_color(self, kind):
        return {
            "Investment": "#27d3a2",
            "Schedule Payment": "#4f8cff",
            "Sale": "#49d17f",
            "Other Inflow": "#4cc9f0",
            "Buy": "#ff9f43",
            "Cost": "#ffb347",
            "Expense": "#ff7a90",
            "Cost Item": "#ffb347",
            "Contractor Payment": "#ff7a90",
            "Refund In": "#7dd3fc",
            "Refund Out": "#f97316",
        }.get(kind, "#d8e4ff")
