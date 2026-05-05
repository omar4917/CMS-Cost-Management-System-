"""
Payment Schedules View for CMS Desktop App.
Track installment plans, overdue payments, and mark payments as paid.
"""

import os
import smtplib
import threading
from datetime import datetime
from email.message import EmailMessage
from tkinter import messagebox

import customtkinter as ctk

from core.database import execute_query
from core.recycle_bin import recycle_and_delete
from core.desktop_utils import as_float, format_date, is_past_date, pick_column


class PaymentSchedulesView(ctk.CTkFrame):
    def __init__(self, parent, user):
        super().__init__(parent, fg_color="transparent")
        self.user = user
        self.template_body_col = pick_column("email_templates", "body", "body_html", "bodyHtml", fallback="body")
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
        header.pack(fill="x", padx=22, pady=(18, 10))

        title_col = ctk.CTkFrame(header, fg_color="transparent")
        title_col.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(
            title_col,
            text="Payment Timeline",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="#f8fafc",
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_col,
            text="Monitor upcoming installments, overdue items, and paid milestones from one surface.",
            font=ctk.CTkFont(size=13),
            text_color="#8ea3c7",
        ).pack(anchor="w", pady=(4, 0))

        ctk.CTkButton(
            header,
            text="+ Add Payment",
            fg_color="#4f8cff",
            hover_color="#3578f6",
            corner_radius=12,
            height=42,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.open_add,
        ).pack(side="right")

        controls = ctk.CTkFrame(hero, fg_color="transparent")
        controls.pack(fill="x", padx=22, pady=(0, 18))

        self.status_var = ctk.StringVar(value="All")
        ctk.CTkOptionMenu(
            controls,
            values=["All", "pending", "paid", "overdue", "partial"],
            variable=self.status_var,
            command=lambda _value: self.load_data(),
            fg_color="#152140",
            button_color="#233154",
            button_hover_color="#31446b",
            dropdown_fg_color="#111d39",
            corner_radius=10,
            height=40,
            width=160,
        ).pack(side="left")

        self.metric_labels = {}
        for key, label, color in [
            ("scheduled", "Scheduled", "#4f8cff"),
            ("overdue", "Overdue", "#ff7a90"),
            ("paid", "Collected", "#27d3a2"),
        ]:
            card = ctk.CTkFrame(
                controls,
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

    def load_data(self):
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        status = self.status_var.get()
        query = (
            "SELECT ps.*, i.name AS investor_name, p.name AS project_name "
            "FROM payment_schedules ps "
            "LEFT JOIN investors i ON ps.investor_id = i.id "
            "LEFT JOIN projects p ON ps.project_id = p.id "
            "WHERE 1=1"
        )
        params = []
        if status != "All":
            if status == "overdue":
                query += " AND (ps.status='overdue' OR (ps.status='pending' AND ps.due_date < CURDATE()))"
            else:
                query += " AND ps.status=%s"
                params.append(status)
        query += " ORDER BY ps.due_date ASC, ps.created_at DESC"

        try:
            payments = execute_query(query, params)
        except Exception as exc:
            ctk.CTkLabel(self.table_frame, text=f"Error: {exc}", text_color="#ef4444").pack(pady=20)
            return

        overdue_rows = [
            row
            for row in payments
            if row.get("status") == "overdue" or (row.get("status") == "pending" and is_past_date(row.get("due_date")))
        ]
        paid_total = 0.0
        for row in payments:
            status = row.get("status")
            if status == "paid":
                paid_total += as_float(row.get("paid_amount") or row.get("amount"))
            elif status == "partial":
                paid_total += as_float(row.get("paid_amount"))
        scheduled_total = sum(as_float(row.get("amount")) for row in payments)

        self.metric_labels["scheduled"].configure(text=f"BDT {scheduled_total:,.0f}")
        self.metric_labels["overdue"].configure(text=str(len(overdue_rows)))
        self.metric_labels["paid"].configure(text=f"BDT {paid_total:,.0f}")

        if not payments:
            empty = ctk.CTkFrame(self.table_frame, fg_color="transparent")
            empty.pack(expand=True, pady=80)
            ctk.CTkLabel(empty, text="No payment schedules", font=ctk.CTkFont(size=20, weight="bold"), text_color="#d8e4ff").pack()
            ctk.CTkLabel(
                empty,
                text="Add an installment plan to start tracking collections and reminders.",
                font=ctk.CTkFont(size=12),
                text_color="#6e84ac",
            ).pack(pady=(6, 0))
            return

        for payment in payments:
            overdue = payment.get("status") == "overdue" or (
                payment.get("status") == "pending" and is_past_date(payment.get("due_date"))
            )
            card = ctk.CTkFrame(
                self.table_frame,
                fg_color="#17112a" if overdue else "#111d39",
                corner_radius=16,
                border_width=1,
                border_color="#45223b" if overdue else "#223356",
            )
            card.pack(fill="x", padx=8, pady=6)

            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=16, pady=(14, 8))

            identity = f"{payment.get('investor_name') or 'Unknown investor'} | {payment.get('project_name') or 'No project'}"
            ctk.CTkLabel(
                top,
                text=identity,
                font=ctk.CTkFont(size=15, weight="bold"),
                text_color="#f8fafc",
            ).pack(side="left")
            ctk.CTkLabel(
                top,
                text=f"BDT {as_float(payment.get('amount')):,.0f}",
                font=ctk.CTkFont(size=15, weight="bold"),
                text_color="#27d3a2" if payment.get("status") == "paid" else "#ffb347",
            ).pack(side="right")

            due_text = format_date(payment.get("due_date"), fmt="%d %b %Y")
            status_text = "OVERDUE" if overdue else (payment.get("status") or "pending").upper()
            detail = f"Due: {due_text}  |  Status: {status_text}"
            if payment.get("notes"):
                detail += f"  |  Notes: {payment['notes']}"
            ctk.CTkLabel(
                card,
                text=detail,
                font=ctk.CTkFont(size=12),
                text_color="#8aa0c8",
                wraplength=820,
                justify="left",
            ).pack(anchor="w", padx=16)

            actions = ctk.CTkFrame(card, fg_color="transparent")
            actions.pack(fill="x", padx=16, pady=(10, 14))

            if payment.get("status") != "paid":
                ctk.CTkButton(
                    actions,
                    text="Mark Paid",
                    width=88,
                    height=32,
                    corner_radius=10,
                    fg_color="#203150",
                    hover_color="#2b426d",
                    command=lambda payment_id=payment["id"]: self.mark_paid(payment_id),
                ).pack(side="left", padx=(0, 6))

            if overdue and payment.get("status") != "paid":
                ctk.CTkButton(
                    actions,
                    text="Send Reminder",
                    width=110,
                    height=32,
                    corner_radius=10,
                    fg_color="#3a2910",
                    hover_color="#5a3f17",
                    text_color="#ffcf7c",
                    command=lambda row=payment: self.send_reminder(row),
                ).pack(side="left", padx=6)

            ctk.CTkButton(
                actions,
                text="Delete",
                width=72,
                height=32,
                corner_radius=10,
                fg_color="#261522",
                hover_color="#4a1d2d",
                text_color="#ff7a90",
                command=lambda payment_id=payment["id"]: self.delete_payment(payment_id),
            ).pack(side="right")

            self._bind_click(card, lambda _event, item=payment: self.open_payment_detail(item))

    def send_reminder(self, payment):
        def _send():
            try:
                investor_rows = execute_query(
                    "SELECT i.name, i.email, t.name AS type FROM investors i "
                    "LEFT JOIN investor_types t ON i.type_id=t.id WHERE i.id=%s",
                    (payment["investor_id"],),
                )
                if not investor_rows or not investor_rows[0].get("email"):
                    self.after(0, lambda: messagebox.showerror("Error", "Investor does not have a valid email address."))
                    return

                template_rows = execute_query(
                    f"SELECT subject, {self.template_body_col} AS body FROM email_templates WHERE name='Payment Overdue Reminder'"
                )
                if not template_rows:
                    self.after(0, lambda: messagebox.showerror("Error", "Template 'Payment Overdue Reminder' was not found."))
                    return

                investor = investor_rows[0]
                template = template_rows[0]
                amount = as_float(payment.get("amount"))
                project_name = payment.get("project_name") or "N/A"
                due = format_date(payment.get("due_date"))

                subject = (
                    template["subject"]
                    .replace("{amount}", f"{amount:,.0f}")
                    .replace("{project}", project_name)
                )
                body = (
                    str(template.get("body") or "")
                    .replace("{name}", investor["name"])
                    .replace("{amount}", f"{amount:,.0f}")
                    .replace("{project}", project_name)
                    .replace("{date}", due)
                )

                admin_email = os.getenv("GMAIL_USER")
                admin_pass = os.getenv("GMAIL_APP_PASS")
                if not admin_email or not admin_pass:
                    self.after(0, lambda: messagebox.showerror("Error", "Gmail SMTP credentials are missing in .env."))
                    return

                message = EmailMessage()
                message.set_content(body)
                message["Subject"] = subject
                message["From"] = admin_email
                message["To"] = investor["email"]

                with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                    smtp.login(admin_email, admin_pass)
                    smtp.send_message(message)

                try:
                    execute_query(
                        "INSERT INTO email_logs (investor_id, to_email, subject, body, status, sent_at) VALUES (%s, %s, %s, %s, 'sent', NOW())",
                        (payment["investor_id"], investor["email"], subject, body),
                        fetch=False,
                    )
                except Exception:
                    pass

                self.after(0, lambda: messagebox.showinfo("Success", f"Reminder sent to {investor['name']}."))
            except Exception as exc:
                self.after(0, lambda: messagebox.showerror("Error", f"Could not send reminder:\n{exc}"))

        threading.Thread(target=_send, daemon=True).start()

    def mark_paid(self, payment_id):
        try:
            execute_query(
                "UPDATE payment_schedules SET status='paid', paid_date=CURDATE(), paid_amount=amount, updated_at=NOW() WHERE id=%s",
                (payment_id,),
                fetch=False,
            )
            self.load_data()
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def open_add(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Add Payment Schedule")
        dialog.geometry("520x520")
        dialog.configure(fg_color="#0b1327")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        ctk.CTkLabel(
            dialog,
            text="Add Payment Schedule",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#f8fafc",
        ).pack(pady=(24, 12))

        form = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=28)

        try:
            investors = execute_query("SELECT id, name FROM investors WHERE is_active=1 ORDER BY name")
            projects = execute_query("SELECT id, name FROM projects ORDER BY name")
        except Exception:
            investors, projects = [], []

        if not investors or not projects:
            dialog.destroy()
            return messagebox.showwarning("Missing Data", "Add at least one active investor and one project first.")

        investor_names = [f"{row['name']} (#{row['id']})" for row in investors]
        project_names = [f"{row['name']} (#{row['id']})" for row in projects]

        for label, variable, values in [
            ("Investor *", ctk.StringVar(value=investor_names[0] if investor_names else ""), investor_names),
            ("Project *", ctk.StringVar(value=project_names[0] if project_names else ""), project_names),
        ]:
            ctk.CTkLabel(form, text=label, text_color="#9bb0d5", font=ctk.CTkFont(size=12, weight="bold")).pack(
                anchor="w", pady=(10, 4)
            )
            menu = ctk.CTkOptionMenu(
                form,
                variable=variable,
                values=values or [""],
                fg_color="#101b35",
                button_color="#233154",
                button_hover_color="#31446b",
                height=40,
                corner_radius=10,
            )
            menu.pack(fill="x")
            if label.startswith("Investor"):
                investor_var = variable
            else:
                project_var = variable

        ctk.CTkLabel(form, text="Installment No", text_color="#9bb0d5", font=ctk.CTkFont(size=12, weight="bold")).pack(
            anchor="w", pady=(10, 4)
        )
        installment_var = ctk.StringVar(value="1")
        ctk.CTkOptionMenu(
            form,
            variable=installment_var,
            values=[str(i) for i in range(1, 25)],
            fg_color="#101b35",
            button_color="#233154",
            button_hover_color="#31446b",
            height=40,
            corner_radius=10,
        ).pack(fill="x")

        ctk.CTkLabel(form, text="Status", text_color="#9bb0d5", font=ctk.CTkFont(size=12, weight="bold")).pack(
            anchor="w", pady=(10, 4)
        )
        status_var = ctk.StringVar(value="pending")
        ctk.CTkOptionMenu(
            form,
            variable=status_var,
            values=["pending", "partial", "paid", "overdue"],
            fg_color="#101b35",
            button_color="#233154",
            button_hover_color="#31446b",
            height=40,
            corner_radius=10,
        ).pack(fill="x")

        entries = {}
        for label, key, placeholder in [
            ("Amount (BDT) *", "amount", "1500000"),
            ("Due Date (YYYY-MM-DD) *", "due_date", datetime.now().strftime("%Y-%m-%d")),
            ("Notes", "notes", "Installment details"),
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
                placeholder_text=placeholder,
            )
            if key == "due_date":
                entry.insert(0, placeholder)
            entry.pack(fill="x")
            entries[key] = entry

        def save():
            try:
                investor_id = int(investor_var.get().split("#")[1].rstrip(")"))
                project_id = int(project_var.get().split("#")[1].rstrip(")"))
                amount = float(entries["amount"].get())
                due_date = entries["due_date"].get().strip()
                execute_query(
                    "INSERT INTO payment_schedules (investor_id, project_id, installment_no, amount, due_date, status, paid_amount, reminder_sent, notes, created_at, updated_at) "
                    "VALUES (%s, %s, %s, %s, %s, %s, 0, 0, %s, NOW(), NOW())",
                    (investor_id, project_id, int(installment_var.get()), amount, due_date, status_var.get(), entries["notes"].get().strip()),
                    fetch=False,
                )
                dialog.destroy()
                self.load_data()
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
            fg_color="#4f8cff",
            hover_color="#3578f6",
            corner_radius=10,
            height=38,
            command=save,
        ).pack(side="right")

    def delete_payment(self, payment_id):
        if not messagebox.askyesno("Delete Payment", "Delete this payment schedule? It will be moved to Recycle Bin."):
            return
        try:
            recycle_and_delete(
                "payment_schedules",
                int(payment_id),
                deleted_by=self.user.get("id"),
                reason="Deleted payment schedule",
            )
            self.load_data()
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def open_payment_detail(self, payment):
        dialog = ctk.CTkToplevel(self)
        dialog.title(payment.get("investor_name") or "Payment Schedule")
        dialog.geometry("640x620")
        dialog.configure(fg_color="#0b1327")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        ctk.CTkLabel(dialog, text=payment.get("investor_name") or "Payment Schedule", font=ctk.CTkFont(size=24, weight="bold"), text_color="#f8fafc").pack(anchor="w", padx=28, pady=(24, 4))
        ctk.CTkLabel(dialog, text=payment.get("project_name") or "No project", font=ctk.CTkFont(size=12), text_color="#8ea3c7").pack(anchor="w", padx=28)

        body = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=(16, 10))
        info = ctk.CTkFrame(body, fg_color="#101b35", corner_radius=16, border_width=1, border_color="#233154")
        info.pack(fill="x")
        for label, value in [
            ("Amount", f"BDT {as_float(payment.get('amount')):,.0f}"),
            ("Installment No", str(payment.get("installment_no") or "-")),
            ("Due Date", format_date(payment.get("due_date"))),
            ("Paid Date", format_date(payment.get("paid_date"))),
            ("Status", str(payment.get("status") or "pending").title()),
            ("Paid Amount", f"BDT {as_float(payment.get('paid_amount')):,.0f}" if payment.get("paid_amount") else "BDT 0"),
        ]:
            row = ctk.CTkFrame(info, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=8)
            ctk.CTkLabel(row, text=label, width=120, anchor="w", font=ctk.CTkFont(size=12, weight="bold"), text_color="#9bb0d5").pack(side="left")
            ctk.CTkLabel(row, text=value, font=ctk.CTkFont(size=12), text_color="#f8fafc", wraplength=380, justify="left").pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(body, text="Notes / Comment", font=ctk.CTkFont(size=14, weight="bold"), text_color="#f8fafc").pack(anchor="w", pady=(14, 6))
        notes_box = ctk.CTkTextbox(body, height=150, fg_color="#101b35", border_color="#233154", border_width=1, corner_radius=12, wrap="word")
        notes_box.pack(fill="x")
        notes_box.insert("1.0", str(payment.get("notes") or "No notes saved."))
        notes_box.configure(state="disabled")

        footer = ctk.CTkFrame(dialog, fg_color="transparent")
        footer.pack(fill="x", padx=24, pady=(0, 20))
        ctk.CTkButton(footer, text="Close", fg_color="#182748", hover_color="#223660", corner_radius=10, height=38, command=dialog.destroy).pack(side="left")

    def _bind_click(self, widget, callback):
        if isinstance(widget, ctk.CTkButton):
            return
        widget.bind("<Button-1>", callback)
        for child in widget.winfo_children():
            self._bind_click(child, callback)
