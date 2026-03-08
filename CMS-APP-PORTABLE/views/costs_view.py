"""
Cost Management View for CMS Desktop App.
Manage cost categories, individual cost items (materials, labor, etc.),
with units, quantities, unit prices, sellers/vendors, and per-project tracking.
"""

import customtkinter as ctk
from tkinter import messagebox
from core.database import execute_query


class CostManagementView(ctk.CTkFrame):
    def __init__(self, parent, user):
        super().__init__(parent, fg_color="transparent")
        self.user = user
        self.build_ui()
        self.load_categories()
        self.load_items()

    def build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(header, text="Cost Management", font=ctk.CTkFont(size=26, weight="bold"),
                    text_color="white").pack(side="left")
        ctk.CTkButton(header, text="+ Add Material / Cost", fg_color="#3b82f6", hover_color="#2563eb",
                     corner_radius=8, height=36, command=self.open_add_item).pack(side="right")
        ctk.CTkButton(header, text="📋 Categories", fg_color="#1e293b", hover_color="#334155",
                     corner_radius=8, height=36, command=self.show_categories).pack(side="right", padx=(0, 10))

        # Filters
        filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        filter_frame.pack(fill="x", pady=(0, 10))

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.load_items())
        ctk.CTkEntry(filter_frame, placeholder_text="Search items (bricks, cement, labor...)",
                    height=38, corner_radius=8, fg_color="#1e293b", border_color="#334155",
                    textvariable=self.search_var, width=300).pack(side="left")

        self.cat_var = ctk.StringVar(value="All Categories")
        self.cat_menu = ctk.CTkOptionMenu(filter_frame, variable=self.cat_var,
                                          values=["All Categories"],
                                          command=lambda _: self.load_items(),
                                          fg_color="#1e293b", button_color="#334155",
                                          height=38, width=200)
        self.cat_menu.pack(side="left", padx=(10, 0))

        self.project_var = ctk.StringVar(value="All Projects")
        self.project_menu = ctk.CTkOptionMenu(filter_frame, variable=self.project_var,
                                              values=["All Projects"],
                                              command=lambda _: self.load_items(),
                                              fg_color="#1e293b", button_color="#334155",
                                              height=38, width=200)
        self.project_menu.pack(side="left", padx=(10, 0))

        # Summary row
        self.summary_frame = ctk.CTkFrame(self, fg_color="#111827", corner_radius=10, height=50)
        self.summary_frame.pack(fill="x", pady=(0, 10))
        self.summary_frame.pack_propagate(False)
        self.summary_label = ctk.CTkLabel(self.summary_frame, text="", font=ctk.CTkFont(size=13),
                                          text_color="#94a3b8")
        self.summary_label.pack(side="left", padx=20)
        self.total_label = ctk.CTkLabel(self.summary_frame, text="", font=ctk.CTkFont(size=15, weight="bold"),
                                        text_color="#10b981")
        self.total_label.pack(side="right", padx=20)

        # Table
        self.table_frame = ctk.CTkScrollableFrame(self, fg_color="#111827", corner_radius=12)
        self.table_frame.pack(fill="both", expand=True)

    def load_categories(self):
        try:
            cats = execute_query("SELECT id, name, icon FROM cost_categories ORDER BY sort_order, name")
            self.categories = cats
            names = ["All Categories"] + [f"{c.get('icon', '📦')} {c['name']}" for c in cats]
            self.cat_menu.configure(values=names)

            projects = execute_query("SELECT id, name FROM projects ORDER BY name")
            self.projects = projects
            proj_names = ["All Projects"] + [p['name'] for p in projects]
            self.project_menu.configure(values=proj_names)
        except Exception as e:
            self.categories = []
            self.projects = []

    def load_items(self):
        for w in self.table_frame.winfo_children():
            w.destroy()

        search = self.search_var.get().strip()
        cat_filter = self.cat_var.get()
        proj_filter = self.project_var.get()

        query = (
            "SELECT ci.*, cc.name as category_name, cc.icon as category_icon, "
            "p.name as project_name "
            "FROM cost_items ci "
            "LEFT JOIN cost_categories cc ON ci.category_id = cc.id "
            "LEFT JOIN projects p ON ci.project_id = p.id "
            "WHERE 1=1"
        )
        params = []

        if search:
            query += " AND (ci.name LIKE %s OR ci.description LIKE %s OR ci.vendor LIKE %s)"
            params.extend([f"%{search}%"] * 3)
        if cat_filter != "All Categories":
            # Extract category name (remove icon prefix)
            cat_name = cat_filter.split(' ', 1)[1] if ' ' in cat_filter else cat_filter
            query += " AND cc.name = %s"
            params.append(cat_name)
        if proj_filter != "All Projects":
            query += " AND p.name = %s"
            params.append(proj_filter)

        query += " ORDER BY ci.created_at DESC"

        try:
            items = execute_query(query, params)
        except Exception as e:
            ctk.CTkLabel(self.table_frame, text=f"Error: {e}", text_color="#ef4444").pack(pady=20)
            return

        # Summary
        total_estimated = sum(float(i.get('estimated_amount', 0) or 0) for i in items)
        total_actual = sum(float(i.get('actual_amount', 0) or 0) for i in items)
        self.summary_label.configure(text=f"{len(items)} items | Estimated: ৳ {total_estimated:,.0f}")
        self.total_label.configure(text=f"Actual Total: ৳ {total_actual:,.0f}")

        if not items:
            empty = ctk.CTkFrame(self.table_frame, fg_color="transparent")
            empty.pack(pady=40)
            ctk.CTkLabel(empty, text="🧱", font=ctk.CTkFont(size=40)).pack()
            ctk.CTkLabel(empty, text="No Cost Items Found", font=ctk.CTkFont(size=16, weight="bold"),
                        text_color="#475569").pack(pady=(10, 5))
            ctk.CTkLabel(empty, text="Add materials, labor, equipment, and other cost items",
                        font=ctk.CTkFont(size=13), text_color="#475569").pack()
            return

        # Table header
        hdr = ctk.CTkFrame(self.table_frame, fg_color="#0f172a")
        hdr.pack(fill="x", padx=5, pady=(5, 0))
        for text, w in [("Item", 180), ("Category", 140), ("Project", 120), ("Qty", 50),
                        ("Unit", 60), ("Unit Price", 90), ("Estimated", 100), ("Actual", 100),
                        ("Vendor/Seller", 120), ("Status", 70), ("", 80)]:
            ctk.CTkLabel(hdr, text=text, font=ctk.CTkFont(size=10, weight="bold"),
                        text_color="#64748b", width=w, anchor="w").pack(side="left", padx=4, pady=8)

        status_colors = {'pending': '#f59e0b', 'approved': '#3b82f6', 'purchased': '#10b981',
                        'delivered': '#8b5cf6', 'cancelled': '#ef4444'}

        for item in items:
            row = ctk.CTkFrame(self.table_frame, fg_color="transparent")
            row.pack(fill="x", padx=5)
            row.bind("<Enter>", lambda e, r=row: r.configure(fg_color="#1e293b"))
            row.bind("<Leave>", lambda e, r=row: r.configure(fg_color="transparent"))

            ctk.CTkLabel(row, text=item.get('name', '') or '', font=ctk.CTkFont(size=12, weight="bold"),
                        text_color="#e2e8f0", width=180, anchor="w").pack(side="left", padx=4, pady=6)

            cat_text = f"{item.get('category_icon', '📦')} {item.get('category_name', '') or '—'}"
            ctk.CTkLabel(row, text=cat_text[:20], font=ctk.CTkFont(size=11),
                        text_color="#94a3b8", width=140, anchor="w").pack(side="left", padx=4)

            ctk.CTkLabel(row, text=(item.get('project_name', '') or '—')[:15], font=ctk.CTkFont(size=11),
                        text_color="#94a3b8", width=120, anchor="w").pack(side="left", padx=4)

            qty = float(item.get('quantity', 0) or 0)
            ctk.CTkLabel(row, text=f"{qty:g}" if qty else '—', font=ctk.CTkFont(size=11),
                        text_color="#e2e8f0", width=50, anchor="w").pack(side="left", padx=4)

            ctk.CTkLabel(row, text=item.get('unit', '') or '—', font=ctk.CTkFont(size=11),
                        text_color="#64748b", width=60, anchor="w").pack(side="left", padx=4)

            unit_price = float(item.get('unit_price', 0) or 0)
            ctk.CTkLabel(row, text=f"৳{unit_price:,.0f}" if unit_price else '—',
                        font=ctk.CTkFont(size=11), text_color="#94a3b8", width=90, anchor="w").pack(side="left", padx=4)

            est = float(item.get('estimated_amount', 0) or 0)
            ctk.CTkLabel(row, text=f"৳{est:,.0f}", font=ctk.CTkFont(size=11),
                        text_color="#f59e0b", width=100, anchor="w").pack(side="left", padx=4)

            act = float(item.get('actual_amount', 0) or 0)
            act_color = "#ef4444" if act > est and est > 0 else "#10b981"
            ctk.CTkLabel(row, text=f"৳{act:,.0f}" if act else '—', font=ctk.CTkFont(size=11, weight="bold"),
                        text_color=act_color, width=100, anchor="w").pack(side="left", padx=4)

            ctk.CTkLabel(row, text=(item.get('vendor', '') or '—')[:15], font=ctk.CTkFont(size=11),
                        text_color="#94a3b8", width=120, anchor="w").pack(side="left", padx=4)

            status = item.get('status', 'pending') or 'pending'
            st_color = status_colors.get(status, '#64748b')
            ctk.CTkLabel(row, text=status, font=ctk.CTkFont(size=10, weight="bold"),
                        text_color=st_color, width=70, anchor="w").pack(side="left", padx=4)

            btn_frame = ctk.CTkFrame(row, fg_color="transparent", width=80)
            btn_frame.pack(side="left", padx=4)
            ctk.CTkButton(btn_frame, text="Edit", width=35, height=24, corner_radius=5,
                         fg_color="#1e293b", hover_color="#334155", font=ctk.CTkFont(size=10),
                         command=lambda i=item: self.open_edit_item(i)).pack(side="left", padx=1)
            ctk.CTkButton(btn_frame, text="Del", width=30, height=24, corner_radius=5,
                         fg_color="#1e293b", hover_color="#7f1d1d", text_color="#ef4444",
                         font=ctk.CTkFont(size=10),
                         command=lambda iid=item['id']: self.delete_item(iid)).pack(side="left", padx=1)

    def open_add_item(self):
        self._open_item_dialog(None)

    def open_edit_item(self, item):
        self._open_item_dialog(item)

    def _open_item_dialog(self, item):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Edit Material/Cost Item" if item else "Add Material/Cost Item")
        dialog.geometry("600x700")
        dialog.configure(fg_color="#0f172a")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Edit Material / Cost" if item else "Add Material / Cost",
                    font=ctk.CTkFont(size=20, weight="bold"), text_color="white").pack(pady=(20, 10))

        form = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=30, pady=(0, 5))

        fields = {}

        def add_field(label, key, default='', **kw):
            ctk.CTkLabel(form, text=label, font=ctk.CTkFont(size=12, weight="bold"),
                        text_color="#94a3b8").pack(anchor="w", pady=(6, 2))
            entry = ctk.CTkEntry(form, height=34, fg_color="#1e293b", border_color="#334155",
                                corner_radius=8, **kw)
            val = str(item.get(key, '') or '') if item else default
            entry.insert(0, val)
            entry.pack(fill="x")
            fields[key] = entry

        add_field("Item Name *", 'name')
        add_field("Description", 'description')

        # Category dropdown
        ctk.CTkLabel(form, text="Category *", font=ctk.CTkFont(size=12, weight="bold"),
                    text_color="#94a3b8").pack(anchor="w", pady=(6, 2))
        cat_names = [c['name'] for c in self.categories]
        current_cat = item.get('category_name', cat_names[0] if cat_names else '') if item else (cat_names[0] if cat_names else '')
        cat_var = ctk.StringVar(value=current_cat)
        if cat_names:
            ctk.CTkOptionMenu(form, values=cat_names, variable=cat_var,
                             fg_color="#1e293b", button_color="#334155", height=34).pack(fill="x")

        # Project dropdown
        ctk.CTkLabel(form, text="Project", font=ctk.CTkFont(size=12, weight="bold"),
                    text_color="#94a3b8").pack(anchor="w", pady=(6, 2))
        proj_names = ["None"] + [p['name'] for p in self.projects]
        current_proj = item.get('project_name', 'None') if item else 'None'
        proj_var = ctk.StringVar(value=current_proj or 'None')
        ctk.CTkOptionMenu(form, values=proj_names, variable=proj_var,
                         fg_color="#1e293b", button_color="#334155", height=34).pack(fill="x")

        # Quantity + Unit row
        qty_frame = ctk.CTkFrame(form, fg_color="transparent")
        qty_frame.pack(fill="x", pady=(6, 0))

        qty_left = ctk.CTkFrame(qty_frame, fg_color="transparent")
        qty_left.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkLabel(qty_left, text="Quantity", font=ctk.CTkFont(size=12, weight="bold"),
                    text_color="#94a3b8").pack(anchor="w", pady=(0, 2))
        qty_entry = ctk.CTkEntry(qty_left, height=34, fg_color="#1e293b", border_color="#334155", corner_radius=8)
        qty_val = str(item.get('quantity', '') or '') if item else ''
        qty_entry.insert(0, qty_val)
        qty_entry.pack(fill="x")
        fields['quantity'] = qty_entry

        qty_right = ctk.CTkFrame(qty_frame, fg_color="transparent")
        qty_right.pack(side="left", fill="x", expand=True, padx=(5, 0))
        ctk.CTkLabel(qty_right, text="Unit", font=ctk.CTkFont(size=12, weight="bold"),
                    text_color="#94a3b8").pack(anchor="w", pady=(0, 2))
        units = ["pcs", "bags", "kg", "ton", "sqft", "sqm", "cft", "rft", "trips",
                 "liters", "gallons", "meters", "feet", "nos", "sets", "rolls",
                 "bundles", "loads", "days", "hours", "months", "lump sum", "lot"]
        unit_var = ctk.StringVar(value=item.get('unit', 'pcs') if item else 'pcs')
        ctk.CTkOptionMenu(qty_right, values=units, variable=unit_var,
                         fg_color="#1e293b", button_color="#334155", height=34).pack(fill="x")

        add_field("Unit Price (৳)", 'unit_price', '0')
        add_field("Estimated Amount (৳)", 'estimated_amount', '0')
        add_field("Actual Amount (৳)", 'actual_amount', '0')
        add_field("Vendor / Seller", 'vendor', placeholder_text="e.g. ABC Bricks Ltd, Local Market")

        # Status
        ctk.CTkLabel(form, text="Status", font=ctk.CTkFont(size=12, weight="bold"),
                    text_color="#94a3b8").pack(anchor="w", pady=(6, 2))
        status_var = ctk.StringVar(value=item.get('status', 'pending') if item else 'pending')
        ctk.CTkOptionMenu(form, values=["pending", "approved", "purchased", "delivered", "cancelled"],
                         variable=status_var, fg_color="#1e293b", button_color="#334155", height=34).pack(fill="x")

        def save():
            name = fields['name'].get().strip()
            if not name:
                messagebox.showwarning("Validation", "Item name is required")
                return

            cat_id = next((c['id'] for c in self.categories if c['name'] == cat_var.get()), None)
            proj_id = next((p['id'] for p in self.projects if p['name'] == proj_var.get()), None)

            try:
                quantity = float(fields['quantity'].get() or 0)
                unit_price = float(fields['unit_price'].get() or 0)
                estimated = float(fields['estimated_amount'].get() or 0)
                actual = float(fields['actual_amount'].get() or 0)

                # Auto-calc estimated if quantity * unit_price and estimated is 0
                if estimated == 0 and quantity > 0 and unit_price > 0:
                    estimated = quantity * unit_price

                if item:
                    execute_query(
                        "UPDATE cost_items SET name=%s, description=%s, category_id=%s, project_id=%s, "
                        "quantity=%s, unit=%s, unit_price=%s, estimated_amount=%s, actual_amount=%s, "
                        "vendor=%s, status=%s, updated_at=NOW() WHERE id=%s",
                        (name, fields['description'].get(), cat_id, proj_id,
                         quantity, unit_var.get(), unit_price, estimated, actual,
                         fields['vendor'].get(), status_var.get(), item['id']),
                        fetch=False)
                else:
                    execute_query(
                        "INSERT INTO cost_items (name, description, category_id, project_id, "
                        "quantity, unit, unit_price, estimated_amount, actual_amount, vendor, status, "
                        "created_at, updated_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),NOW())",
                        (name, fields['description'].get(), cat_id, proj_id,
                         quantity, unit_var.get(), unit_price, estimated, actual,
                         fields['vendor'].get(), status_var.get()),
                        fetch=False)

                dialog.destroy()
                self.load_items()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=(5, 20))
        ctk.CTkButton(btn_frame, text="Cancel", fg_color="#1e293b", hover_color="#334155",
                     height=38, command=dialog.destroy).pack(side="left")
        ctk.CTkButton(btn_frame, text="Save", fg_color="#3b82f6", hover_color="#2563eb",
                     height=38, command=save).pack(side="right")

    def delete_item(self, item_id):
        if messagebox.askyesno("Confirm", "Delete this cost item?"):
            try:
                execute_query("DELETE FROM cost_items WHERE id=%s", (item_id,), fetch=False)
                self.load_items()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def show_categories(self):
        """Show cost categories in a popup."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Cost Categories")
        dialog.geometry("600x600")
        dialog.configure(fg_color="#0f172a")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Cost Categories", font=ctk.CTkFont(size=20, weight="bold"),
                    text_color="white").pack(pady=(20, 15))

        scroll = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        try:
            categories = execute_query("SELECT * FROM cost_categories ORDER BY sort_order, name")
            for cat in categories:
                row = ctk.CTkFrame(scroll, fg_color="#111827", corner_radius=8)
                row.pack(fill="x", pady=3)
                ctk.CTkLabel(row, text=cat.get('icon', '📦'), font=ctk.CTkFont(size=22),
                            width=40).pack(side="left", padx=(12, 5), pady=8)
                info = ctk.CTkFrame(row, fg_color="transparent")
                info.pack(side="left", fill="x", expand=True, padx=5)
                ctk.CTkLabel(info, text=cat['name'], font=ctk.CTkFont(size=13, weight="bold"),
                            text_color="#e2e8f0", anchor="w").pack(anchor="w")
                if cat.get('description'):
                    ctk.CTkLabel(info, text=cat['description'], font=ctk.CTkFont(size=11),
                                text_color="#64748b", anchor="w", wraplength=400).pack(anchor="w")
                if cat.get('is_default'):
                    ctk.CTkLabel(row, text="Default", font=ctk.CTkFont(size=10, weight="bold"),
                                text_color="#3b82f6").pack(side="right", padx=12)
        except Exception as e:
            ctk.CTkLabel(scroll, text=f"Error: {e}", text_color="#ef4444").pack(pady=20)
