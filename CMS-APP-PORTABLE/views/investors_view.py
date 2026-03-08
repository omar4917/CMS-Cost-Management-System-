"""
Investors View for CMS Desktop App.
Premium design with search, data table, and financial summary.
"""

import customtkinter as ctk
from tkinter import messagebox
from core.database import execute_query


class InvestorsView(ctk.CTkFrame):
    def __init__(self, parent, user):
        super().__init__(parent, fg_color="transparent")
        self.user = user
        self.investor_types = []
        self.build_ui()
        self.load_types()
        self.load_data()

    def build_ui(self):
        # ── Header ──
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(5, 18))

        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left")
        ctk.CTkLabel(title_frame, text="👥  Investors",
                     font=ctk.CTkFont(size=24, weight="bold"),
                     text_color="#f1f5f9").pack(side="left")

        ctk.CTkButton(header, text="＋  Add Investor", fg_color="#3b82f6",
                      hover_color="#2563eb", corner_radius=10, height=38,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=self.open_add).pack(side="right")

        # ── Search Bar ──
        search_frame = ctk.CTkFrame(self, fg_color="#111827", corner_radius=12,
                                     border_width=1, border_color="#1e293b")
        search_frame.pack(fill="x", pady=(0, 15))

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.load_data())
        ctk.CTkEntry(search_frame, placeholder_text="🔍  Search by name, email, or company...",
                     height=42, corner_radius=10, fg_color="transparent", border_width=0,
                     textvariable=self.search_var,
                     font=ctk.CTkFont(size=13),
                     text_color="#e2e8f0",
                     placeholder_text_color="#475569").pack(fill="x", padx=12, pady=6)

        # ── Table ──
        self.table_frame = ctk.CTkScrollableFrame(self, fg_color="#111827", corner_radius=14,
                                                   border_width=1, border_color="#1e293b",
                                                   scrollbar_button_color="#1e293b",
                                                   scrollbar_button_hover_color="#334155")
        self.table_frame.pack(fill="both", expand=True)

    def load_types(self):
        try:
            self.investor_types = execute_query("SELECT * FROM investor_types ORDER BY name")
        except:
            self.investor_types = []

    def load_data(self):
        for w in self.table_frame.winfo_children():
            w.destroy()

        search = self.search_var.get().strip()
        query = ("SELECT i.*, it.name as type_name, it.color as type_color "
                "FROM investors i LEFT JOIN investor_types it ON i.type_id = it.id "
                "WHERE 1=1")
        params = []
        if search:
            query += " AND (i.name LIKE %s OR i.email LIKE %s OR i.company LIKE %s)"
            params.extend([f"%{search}%"] * 3)
        query += " ORDER BY i.created_at DESC"

        try:
            investors = execute_query(query, params)
        except Exception as e:
            ctk.CTkLabel(self.table_frame, text=f"⚠️ Error: {e}", text_color="#ef4444",
                        font=ctk.CTkFont(size=13)).pack(pady=20)
            return

        if not investors:
            empty = ctk.CTkFrame(self.table_frame, fg_color="transparent")
            empty.pack(expand=True, pady=60)
            ctk.CTkLabel(empty, text="👥", font=ctk.CTkFont(size=40)).pack()
            ctk.CTkLabel(empty, text="No investors found",
                        font=ctk.CTkFont(size=16, weight="bold"),
                        text_color="#475569").pack(pady=(10, 4))
            ctk.CTkLabel(empty, text="Add your first investor to get started",
                        font=ctk.CTkFont(size=13), text_color="#334155").pack()
            return

        # ── Table Header ──
        hdr = ctk.CTkFrame(self.table_frame, fg_color="#0c1222", corner_radius=8)
        hdr.pack(fill="x", padx=8, pady=(8, 4))
        cols = [("Name", 170), ("Email", 170), ("Phone", 120), ("Type", 110), ("Status", 80), ("Actions", 130)]
        for text, w in cols:
            ctk.CTkLabel(hdr, text=text.upper(), font=ctk.CTkFont(size=10, weight="bold"),
                        text_color="#475569", width=w, anchor="w").pack(side="left", padx=8, pady=10)

        # ── Table Rows ──
        for idx, inv in enumerate(investors):
            bg = "#0f172a" if idx % 2 == 0 else "transparent"
            row = ctk.CTkFrame(self.table_frame, fg_color=bg, corner_radius=6)
            row.pack(fill="x", padx=8, pady=1)
            row.bind("<Enter>", lambda e, r=row: r.configure(fg_color="#1e293b"))
            row.bind("<Leave>", lambda e, r=row, b=bg: r.configure(fg_color=b))

            ctk.CTkLabel(row, text=inv['name'] or '', font=ctk.CTkFont(size=13, weight="bold"),
                        text_color="#e2e8f0", width=170, anchor="w").pack(side="left", padx=8, pady=10)
            ctk.CTkLabel(row, text=inv.get('email', '') or '—', font=ctk.CTkFont(size=12),
                        text_color="#94a3b8", width=170, anchor="w").pack(side="left", padx=8)
            ctk.CTkLabel(row, text=inv.get('phone', '') or '—', font=ctk.CTkFont(size=12),
                        text_color="#94a3b8", width=120, anchor="w").pack(side="left", padx=8)

            type_color = inv.get('type_color', '#3b82f6') or '#3b82f6'
            type_name = inv.get('type_name', 'N/A') or 'N/A'
            type_badge = ctk.CTkFrame(row, fg_color="transparent", width=110)
            type_badge.pack(side="left", padx=8)
            type_badge.pack_propagate(False)
            ctk.CTkLabel(type_badge, text=type_name, font=ctk.CTkFont(size=11, weight="bold"),
                        text_color=type_color, anchor="w").pack(side="left")

            status_color = "#10b981" if inv.get('is_active') else "#ef4444"
            status_text = "Active" if inv.get('is_active') else "Inactive"
            ctk.CTkLabel(row, text=f"● {status_text}",
                        font=ctk.CTkFont(size=11, weight="bold"), text_color=status_color,
                        width=80, anchor="w").pack(side="left", padx=8)

            btn_frame = ctk.CTkFrame(row, fg_color="transparent", width=130)
            btn_frame.pack(side="left", padx=8)
            ctk.CTkButton(btn_frame, text="View", width=42, height=28, corner_radius=6,
                         fg_color="#1e293b", hover_color="#334155", font=ctk.CTkFont(size=11),
                         border_width=1, border_color="#334155",
                         command=lambda i=inv: self.view_summary(i)).pack(side="left", padx=2)
            ctk.CTkButton(btn_frame, text="Edit", width=42, height=28, corner_radius=6,
                         fg_color="#1e293b", hover_color="#334155", font=ctk.CTkFont(size=11),
                         border_width=1, border_color="#334155",
                         command=lambda i=inv: self.open_edit(i)).pack(side="left", padx=2)
            ctk.CTkButton(btn_frame, text="Del", width=38, height=28, corner_radius=6,
                         fg_color="transparent", hover_color="#7f1d1d", text_color="#ef4444",
                         font=ctk.CTkFont(size=11), border_width=1, border_color="#7f1d1d",
                         command=lambda iid=inv['id']: self.delete_investor(iid)).pack(side="left", padx=2)

        # ── Footer count ──
        footer = ctk.CTkFrame(self.table_frame, fg_color="transparent")
        footer.pack(fill="x", padx=10, pady=(8, 4))
        ctk.CTkLabel(footer, text=f"Showing {len(investors)} investor{'s' if len(investors) != 1 else ''}",
                    font=ctk.CTkFont(size=11), text_color="#475569").pack(side="left")

    def view_summary(self, investor):
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"{investor['name']} — Financial Summary")
        dialog.geometry("620x520")
        dialog.configure(fg_color="#0f172a")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        # Name header
        ctk.CTkLabel(dialog, text=investor['name'], font=ctk.CTkFont(size=22, weight="bold"),
                    text_color="white").pack(pady=(20, 5))
        ctk.CTkLabel(dialog, text=investor.get('type_name', '') or 'Investor',
                    font=ctk.CTkFont(size=13), text_color="#64748b").pack()

        try:
            invested = execute_query(
                "SELECT COALESCE(SUM(amount), 0) as total FROM investments WHERE investor_id=%s AND status='confirmed'",
                (investor['id'],))
            paid = execute_query(
                "SELECT COALESCE(SUM(amount), 0) as total FROM payment_schedules WHERE investor_id=%s AND status='paid'",
                (investor['id'],))
            total_inv = float(invested[0]['total'] or 0)
            total_paid = float(paid[0]['total'] or 0)

            stats = ctk.CTkFrame(dialog, fg_color="transparent")
            stats.pack(fill="x", padx=30, pady=20)
            for i in range(3):
                stats.grid_columnconfigure(i, weight=1)

            for col, (label, value, color) in enumerate([
                ("Total Invested", f"৳ {total_inv:,.0f}", "#10b981"),
                ("Total Paid", f"৳ {total_paid:,.0f}", "#3b82f6"),
                ("Unpaid / Due", f"৳ {max(total_inv - total_paid, 0):,.0f}", "#ef4444"),
            ]):
                card = ctk.CTkFrame(stats, fg_color="#111827", corner_radius=12,
                                   border_width=1, border_color="#1e293b")
                card.grid(row=0, column=col, padx=5, sticky="nsew")
                ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=18, weight="bold"),
                            text_color=color).pack(pady=(15, 3), padx=10)
                ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=11),
                            text_color="#64748b").pack(pady=(0, 12))

            # Investment history
            history = execute_query(
                "SELECT inv.amount, inv.date, inv.payment_method, p.name as project_name "
                "FROM investments inv LEFT JOIN projects p ON inv.project_id = p.id "
                "WHERE inv.investor_id=%s ORDER BY inv.date DESC LIMIT 10",
                (investor['id'],))

            if history:
                ctk.CTkLabel(dialog, text="Investment History", font=ctk.CTkFont(size=15, weight="bold"),
                            text_color="white").pack(anchor="w", padx=30, pady=(10, 5))
                for h in history:
                    row = ctk.CTkFrame(dialog, fg_color="#111827", corner_radius=8,
                                      border_width=1, border_color="#1e293b")
                    row.pack(fill="x", padx=30, pady=2)
                    ctk.CTkLabel(row, text=h.get('project_name', '') or '—', font=ctk.CTkFont(size=12),
                                text_color="#e2e8f0", width=150, anchor="w").pack(side="left", padx=10, pady=8)
                    ctk.CTkLabel(row, text=f"৳ {float(h.get('amount', 0)):,.0f}",
                                font=ctk.CTkFont(size=12, weight="bold"), text_color="#10b981",
                                width=100).pack(side="left", padx=5)
                    date_str = h['date'].strftime("%d %b %Y") if h.get('date') else '—'
                    ctk.CTkLabel(row, text=date_str, font=ctk.CTkFont(size=11),
                                text_color="#64748b").pack(side="left", padx=5)
                    ctk.CTkLabel(row, text=(h.get('payment_method', '') or '').replace('_', ' '),
                                font=ctk.CTkFont(size=11), text_color="#475569").pack(side="right", padx=10)

        except Exception as e:
            ctk.CTkLabel(dialog, text=f"Error: {e}", text_color="#ef4444").pack(pady=20)

    def open_add(self):
        self._open_dialog(None)

    def open_edit(self, investor):
        self._open_dialog(investor)

    def _open_dialog(self, investor):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Edit Investor" if investor else "Add Investor")
        dialog.geometry("520x580")
        dialog.configure(fg_color="#0f172a")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Edit Investor" if investor else "Add Investor",
                    font=ctk.CTkFont(size=20, weight="bold"), text_color="white").pack(pady=(20, 15))

        form = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=30)

        fields = {}
        def add_field(label, key, default=''):
            ctk.CTkLabel(form, text=label, font=ctk.CTkFont(size=12, weight="bold"),
                        text_color="#94a3b8").pack(anchor="w", pady=(10, 3))
            entry = ctk.CTkEntry(form, height=40, fg_color="#1e293b", border_color="#334155",
                                corner_radius=10, font=ctk.CTkFont(size=13))
            val = str(investor.get(key, '') or '') if investor else default
            entry.insert(0, val)
            entry.pack(fill="x")
            fields[key] = entry

        add_field("Full Name *", 'name')
        add_field("Email", 'email')
        add_field("Phone", 'phone')
        add_field("Company", 'company')
        add_field("National ID", 'national_id')
        add_field("Bank Name", 'bank_name')
        add_field("Bank Account", 'bank_account')

        # Type dropdown
        ctk.CTkLabel(form, text="Investor Type", font=ctk.CTkFont(size=12, weight="bold"),
                    text_color="#94a3b8").pack(anchor="w", pady=(10, 3))
        type_names = [t['name'] for t in self.investor_types]
        current_type = next((t['name'] for t in self.investor_types if investor and t['id'] == investor.get('type_id')), type_names[0] if type_names else '')
        type_var = ctk.StringVar(value=current_type)
        if type_names:
            ctk.CTkOptionMenu(form, values=type_names, variable=type_var,
                             fg_color="#1e293b", button_color="#334155", height=40,
                             corner_radius=10, font=ctk.CTkFont(size=13)).pack(fill="x")

        def save():
            name = fields['name'].get().strip()
            if not name:
                messagebox.showwarning("Validation", "Name is required")
                return
            type_id = next((t['id'] for t in self.investor_types if t['name'] == type_var.get()), None)
            try:
                if investor:
                    execute_query(
                        "UPDATE investors SET name=%s, email=%s, phone=%s, company=%s, "
                        "national_id=%s, bank_name=%s, bank_account=%s, type_id=%s, updated_at=NOW() WHERE id=%s",
                        (name, fields['email'].get(), fields['phone'].get(), fields['company'].get(),
                         fields['national_id'].get(), fields['bank_name'].get(), fields['bank_account'].get(),
                         type_id, investor['id']),
                        fetch=False)
                else:
                    execute_query(
                        "INSERT INTO investors (name, email, phone, company, national_id, bank_name, bank_account, type_id, is_active, created_at, updated_at) "
                        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,1,NOW(),NOW())",
                        (name, fields['email'].get(), fields['phone'].get(), fields['company'].get(),
                         fields['national_id'].get(), fields['bank_name'].get(), fields['bank_account'].get(), type_id),
                        fetch=False)
                dialog.destroy()
                self.load_data()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=(10, 20))
        ctk.CTkButton(btn_frame, text="Cancel", fg_color="#1e293b", hover_color="#334155",
                     height=40, corner_radius=10, border_width=1, border_color="#334155",
                     command=dialog.destroy).pack(side="left")
        ctk.CTkButton(btn_frame, text="Save", fg_color="#3b82f6", hover_color="#2563eb",
                     height=40, corner_radius=10, font=ctk.CTkFont(weight="bold"),
                     command=save).pack(side="right")

    def delete_investor(self, investor_id):
        if messagebox.askyesno("Confirm", "Delete this investor?"):
            try:
                execute_query("DELETE FROM investors WHERE id=%s", (investor_id,), fetch=False)
                self.load_data()
            except Exception as e:
                messagebox.showerror("Error", str(e))
