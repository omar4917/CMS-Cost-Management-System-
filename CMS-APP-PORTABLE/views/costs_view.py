"""
Cost management view for the desktop app.
"""

from datetime import datetime
from tkinter import messagebox, ttk
import tkinter as tk

import customtkinter as ctk

from core.database import execute_query
from core.recycle_bin import recycle_and_delete, recycle_and_delete_many


UNIT_OPTIONS = ["pcs", "bags", "kg", "ton", "sqft", "sqm", "cft", "rft", "trips", "days", "hours", "months", "lot"]
STATUS_OPTIONS = ["pending", "approved", "purchased", "delivered", "cancelled"]

TRACKER_TABLE_COLUMNS = [
    ("receive_date", "Receive DATE", 105, "center"),
    ("receive_detail", "Receive DETAIL", 230, "w"),
    ("receive_amount", "Receive AMOUNT", 115, "e"),
    ("received_from", "RECEIVED FROM", 160, "w"),
    ("cost_date", "Cost DATE", 105, "center"),
    ("cost_detail", "Cost DETAIL", 260, "w"),
    ("cost_amount", "Cost AMOUNT", 115, "e"),
    ("pay_to", "PAY TO", 160, "w"),
    ("unit", "Unit", 80, "w"),
    ("unit_rate", "Unit Rate", 100, "e"),
    ("qty", "Qty", 70, "e"),
    ("qty_cft", "Qty (CFT)", 90, "e"),
    ("remarks", "REMARKS", 220, "w"),
    ("cost_head_materials", "COST HEAD (Materials)", 190, "w"),
    ("structure_or_finishing", "Structure/Finishing", 150, "w"),
    ("cost_summary_1", "Cost Summary 1", 170, "w"),
    ("category_boq_mapping", "Category BOQ Mapping", 185, "w"),
    ("cost_head_floors", "COST HEAD (Floors)", 150, "w"),
    ("cost_head_project", "COST HEAD (Project & Office)", 210, "w"),
    ("cost_head_months", "COST HEAD (Months)", 135, "w"),
]


def _safe_float(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _money(value):
    return f"BDT {_safe_float(value):,.0f}"


def _date_text(value):
    if not value:
        return "-"
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return text


def _text(value):
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() == "nan":
        return ""
    return text


def _cell_date(value):
    text = _date_text(value)
    return "" if text == "-" else text


def _num_text(value):
    number = _safe_float(value)
    if number == 0:
        return ""
    if abs(number - round(number)) < 1e-9:
        return f"{int(round(number)):,}"
    return f"{number:,.2f}".rstrip("0").rstrip(".")


class CostManagementView(ctk.CTkFrame):
    def __init__(self, parent, user):
        super().__init__(parent, fg_color="transparent")
        self.user = user
        self.categories = []  # COST HEAD (Materials)
        self.projects = []  # projects table rows (id/name)
        self.currency_codes = ["BDT"]
        self.items_by_id = {}
        self.bulk_select_var = ctk.BooleanVar(value=False)
        self.extra_labels = {}  # {field_key: label} loaded dynamically
        self.build_ui()
        self.load_categories()
        self._refresh_extra_labels()
        self.load_items()

    def build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(header, text="Cost Management", font=ctk.CTkFont(size=26, weight="bold"), text_color="white").pack(side="left")
        ctk.CTkButton(header, text="+ Add Material / Cost", fg_color="#3b82f6", hover_color="#2563eb", corner_radius=8, height=36, command=self.open_add_item).pack(side="right")
        ctk.CTkButton(header, text="Delete Selected", fg_color="#ef4444", hover_color="#dc2626", corner_radius=8, height=36, command=self.delete_selected_items).pack(side="right", padx=(0, 10))
        ctk.CTkButton(header, text="Cost Heads", fg_color="#1e293b", hover_color="#334155", corner_radius=8, height=36, command=self.show_cost_heads).pack(side="right", padx=(0, 10))

        filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        filter_frame.pack(fill="x", pady=(0, 10))
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.load_items())
        ctk.CTkEntry(filter_frame, placeholder_text="Search items, vendors, invoices, or notes...", height=38, corner_radius=8, fg_color="#1e293b", border_color="#334155", textvariable=self.search_var, width=320).pack(side="left")

        self.cat_var = ctk.StringVar(value="All Materials")
        self.cat_menu = ctk.CTkOptionMenu(filter_frame, variable=self.cat_var, values=["All Materials"], command=lambda _: self.load_items(), fg_color="#1e293b", button_color="#334155", height=38, width=230)
        self.cat_menu.pack(side="left", padx=(10, 0))

        self.project_var = ctk.StringVar(value="All Projects")
        self.project_menu = ctk.CTkOptionMenu(filter_frame, variable=self.project_var, values=["All Projects"], command=lambda _: self.load_items(), fg_color="#1e293b", button_color="#334155", height=38, width=250)
        self.project_menu.pack(side="left", padx=(10, 0))

        ctk.CTkCheckBox(
            filter_frame,
            text="Bulk select",
            variable=self.bulk_select_var,
            fg_color="#4f8cff",
            hover_color="#3578f6",
            text_color="#c8d6f1",
        ).pack(side="right")
        ctk.CTkLabel(
            filter_frame,
            text="Tip: Ctrl+Click selects multiple rows",
            font=ctk.CTkFont(size=11),
            text_color="#64748b",
        ).pack(side="right", padx=(0, 14))

        self.summary_frame = ctk.CTkFrame(self, fg_color="#111827", corner_radius=10, height=50)
        self.summary_frame.pack(fill="x", pady=(0, 10))
        self.summary_frame.pack_propagate(False)
        self.summary_label = ctk.CTkLabel(self.summary_frame, text="", font=ctk.CTkFont(size=13), text_color="#94a3b8")
        self.summary_label.pack(side="left", padx=20)
        self.total_label = ctk.CTkLabel(self.summary_frame, text="", font=ctk.CTkFont(size=15, weight="bold"), text_color="#10b981")
        self.total_label.pack(side="right", padx=20)

        self.table_container = ctk.CTkFrame(self, fg_color="#111827", corner_radius=12)
        self.table_container.pack(fill="both", expand=True)
        self.table_container.grid_columnconfigure(0, weight=1)
        self.table_container.grid_rowconfigure(0, weight=1)

        self._init_tracker_table()

    def load_categories(self):
        selected_material = self.cat_var.get()
        selected_project = self.project_var.get()
        try:
            materials = execute_query(
                "SELECT DISTINCT cost_head_materials AS name "
                "FROM cost_items "
                "WHERE cost_head_materials IS NOT NULL AND TRIM(cost_head_materials) <> '' "
                "ORDER BY name"
            )
            self.categories = [row.get("name") for row in (materials or []) if row.get("name")]
            self.projects = execute_query("SELECT id, name FROM projects ORDER BY name") or []

            self.cat_menu.configure(values=["All Materials"] + self.categories)
            self.project_menu.configure(values=["All Projects"] + [row.get("name") for row in self.projects if row.get("name")])

            if selected_material in self.categories:
                self.cat_var.set(selected_material)
            else:
                self.cat_var.set("All Materials")

            if selected_project in [row.get("name") for row in self.projects]:
                self.project_var.set(selected_project)
            else:
                self.project_var.set("All Projects")

            try:
                currencies = execute_query("SELECT code FROM currencies ORDER BY code")
                self.currency_codes = [row["code"] for row in currencies] or ["BDT"]
            except Exception:
                self.currency_codes = ["BDT"]
        except Exception:
            self.categories = []
            self.projects = []
            self.cat_menu.configure(values=["All Materials"])
            self.project_menu.configure(values=["All Projects"])
            self.cat_var.set("All Materials")
            self.project_var.set("All Projects")
            self.currency_codes = ["BDT"]

    def _init_tracker_table(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure(
            "Tracker.Treeview",
            background="#111827",
            fieldbackground="#111827",
            foreground="#e2e8f0",
            rowheight=30,
            borderwidth=0,
            relief="flat",
        )
        style.map(
            "Tracker.Treeview",
            background=[("selected", "#1e293b")],
            foreground=[("selected", "#f8fafc")],
        )
        style.configure(
            "Tracker.Treeview.Heading",
            background="#0f172a",
            foreground="#94a3b8",
            relief="flat",
            font=("Segoe UI", 9, "bold"),
        )

        columns = [key for key, _label, _w, _a in TRACKER_TABLE_COLUMNS]
        self.tree = ttk.Treeview(
            self.table_container,
            columns=columns,
            show="headings",
            style="Tracker.Treeview",
            selectmode="extended",
        )
        for key, label, width, anchor in TRACKER_TABLE_COLUMNS:
            self.tree.heading(key, text=label, anchor=anchor)
            self.tree.column(
                key,
                width=width,
                anchor=anchor,
                stretch=key in {"receive_detail", "cost_detail", "remarks"},
            )

        self.tree.tag_configure("even", background="#111827")
        self.tree.tag_configure("odd", background="#0b1220")

        v_scroll = ttk.Scrollbar(self.table_container, orient="vertical", command=self.tree.yview)
        h_scroll = ttk.Scrollbar(self.table_container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        self.table_container.grid_columnconfigure(1, weight=0)
        self.table_container.grid_rowconfigure(1, weight=0)

        self.tree.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=(10, 0))
        v_scroll.grid(row=0, column=1, sticky="ns", padx=(0, 10), pady=(10, 0))
        h_scroll.grid(row=1, column=0, sticky="ew", padx=(10, 0), pady=(0, 10))

        self.tree.bind("<Button-1>", self._on_tree_click, add=True)
        self.tree.bind("<Double-1>", lambda _e: self.open_selected_item())
        self.tree.bind("<Return>", lambda _e: self.open_selected_item())
        self.tree.bind("<Delete>", lambda _e: self.delete_selected_items())

        # Extra dynamic columns will be added in load_items
        self._extra_column_keys = []

        self.table_overlay = ctk.CTkLabel(
            self.table_container,
            text="",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#475569",
        )

    def _clear_tracker_table(self):
        for iid in self.tree.get_children():
            self.tree.delete(iid)

    def _show_table_overlay(self, text, color="#475569"):
        self.table_overlay.configure(text=text, text_color=color)
        self.table_overlay.place(relx=0.5, rely=0.5, anchor="center")

    def _hide_table_overlay(self):
        self.table_overlay.place_forget()

    def open_selected_item(self):
        if bool(self.bulk_select_var.get()):
            return
        selected = self.tree.selection()
        if not selected:
            return
        try:
            item_id = int(selected[0])
        except ValueError:
            return
        item = self.items_by_id.get(item_id)
        if item:
            self.open_item_detail(item)

    def _on_tree_click(self, event):
        """Optional click-to-multi-select without holding Ctrl (Bulk select mode)."""
        if not bool(self.bulk_select_var.get()):
            return

        try:
            region = self.tree.identify_region(event.x, event.y)
            if region not in {"cell", "tree"}:
                return
            iid = self.tree.identify_row(event.y)
            if not iid:
                return
            if iid in self.tree.selection():
                self.tree.selection_remove(iid)
            else:
                self.tree.selection_add(iid)
            return "break"
        except Exception:
            return

    def _refresh_extra_labels(self):
        """Load custom field labels for the current project filter (or all)."""
        self.extra_labels = {}
        try:
            project_filter = self.project_var.get() if hasattr(self, 'project_var') else "All Projects"
            if project_filter != "All Projects":
                project_id = next((row.get("id") for row in self.projects if row.get("name") == project_filter), None)
                if project_id is not None:
                    rows = execute_query(
                        "SELECT field_key, label FROM custom_field_labels WHERE project_id=%s ORDER BY sort_order",
                        (project_id,),
                    )
                    self.extra_labels = {r["field_key"]: r["label"] for r in (rows or [])}
                    return
            # All Projects — union of all labels
            rows = execute_query(
                "SELECT DISTINCT field_key, label FROM custom_field_labels ORDER BY sort_order",
            )
            self.extra_labels = {r["field_key"]: r["label"] for r in (rows or [])}
        except Exception:
            pass

    def _rebuild_extra_columns(self):
        """Add/remove extra columns in the treeview based on current extra_labels."""
        # Remove old extra columns
        for key in self._extra_column_keys:
            try:
                self.tree.heading(key, text="")
                self.tree.column(key, width=0, stretch=False)
            except Exception:
                pass

        # Determine which extras actually have data
        active_extras = [f"extra_{i}" for i in range(1, 11) if f"extra_{i}" in self.extra_labels]
        self._extra_column_keys = active_extras

        if not active_extras:
            # Reset columns to base only
            base_columns = [key for key, _l, _w, _a in TRACKER_TABLE_COLUMNS]
            self.tree["columns"] = base_columns
            for key, label, width, anchor in TRACKER_TABLE_COLUMNS:
                self.tree.heading(key, text=label, anchor=anchor)
                self.tree.column(key, width=width, anchor=anchor, stretch=key in {"receive_detail", "cost_detail", "remarks"})
            return

        # Rebuild columns = base + extras
        base_columns = [key for key, _l, _w, _a in TRACKER_TABLE_COLUMNS]
        all_columns = base_columns + active_extras
        self.tree["columns"] = all_columns

        # Re-apply base headings
        for key, label, width, anchor in TRACKER_TABLE_COLUMNS:
            self.tree.heading(key, text=label, anchor=anchor)
            self.tree.column(key, width=width, anchor=anchor, stretch=key in {"receive_detail", "cost_detail", "remarks"})

        # Apply extra headings
        for key in active_extras:
            label = self.extra_labels.get(key, key)
            self.tree.heading(key, text=label, anchor="w")
            self.tree.column(key, width=150, anchor="w", stretch=False)

    def load_items(self):
        self._refresh_extra_labels()
        self._rebuild_extra_columns()
        self._clear_tracker_table()
        self._hide_table_overlay()

        query = (
            "SELECT ci.*, p.name AS project_name, cc.name AS category_name "
            "FROM cost_items ci "
            "LEFT JOIN projects p ON ci.project_id = p.id "
            "LEFT JOIN cost_categories cc ON ci.category_id = cc.id "
            "WHERE 1=1"
        )
        params = []
        search = self.search_var.get().strip()
        if search:
            query += (
                " AND ("
                "ci.receive_detail LIKE %s OR ci.received_from LIKE %s OR "
                "ci.cost_detail LIKE %s OR ci.pay_to LIKE %s OR "
                "ci.unit LIKE %s OR ci.remarks LIKE %s OR "
                "ci.cost_head_materials LIKE %s OR ci.structure_or_finishing LIKE %s OR "
                "ci.cost_summary_1 LIKE %s OR ci.category_boq_mapping LIKE %s OR "
                "ci.cost_head_floors LIKE %s OR ci.cost_head_project LIKE %s OR "
                "ci.cost_head_months LIKE %s OR "
                "ci.description LIKE %s OR ci.name LIKE %s OR "
                "ci.vendor LIKE %s OR ci.invoice_no LIKE %s OR ci.notes LIKE %s OR "
                "p.name LIKE %s OR cc.name LIKE %s"
                ")"
            )
            params.extend([f"%{search}%"] * 20)

        if self.cat_var.get() != "All Materials":
            selected = self.cat_var.get()
            query += " AND (ci.cost_head_materials=%s OR cc.name=%s)"
            params.extend([selected, selected])

        if self.project_var.get() != "All Projects":
            selected = self.project_var.get()
            project_id = next((row.get("id") for row in self.projects if row.get("name") == selected), None)
            if project_id is not None:
                query += " AND (ci.project_id=%s OR ci.cost_head_project=%s)"
                params.extend([project_id, selected])
            else:
                query += " AND (p.name=%s OR ci.cost_head_project=%s)"
                params.extend([selected, selected])

        query += " ORDER BY COALESCE(ci.cost_date, ci.receive_date, ci.date, ci.created_at) DESC, ci.id DESC"

        try:
            items = execute_query(query, params)
        except Exception as exc:
            self._show_table_overlay(f"Error: {exc}", color="#ef4444")
            return

        self.items_by_id = {int(item["id"]): item for item in (items or []) if item.get("id") is not None}

        total_receive = sum(_safe_float(i.get("receive_amount")) for i in (items or []))
        total_cost = 0.0
        for item in items or []:
            cost_value = _safe_float(item.get("cost_amount"))
            if cost_value == 0:
                cost_value = _safe_float(item.get("actual_amount"))
            if cost_value == 0:
                cost_value = _safe_float(item.get("estimated_amount"))
            total_cost += cost_value

        in_hand = total_receive - total_cost
        self.summary_label.configure(text=f"{len(items or [])} items | Total Receive: {_money(total_receive)} | In Hand: {_money(in_hand)}")
        self.total_label.configure(text=f"Total Expenditure: {_money(total_cost)}")

        if not items:
            self._show_table_overlay("No cost items found")
            return

        # If the view was opened before importing the tracker, refresh dropdown values once data exists.
        if not self.categories and not self.projects:
            try:
                self.load_categories()
            except Exception:
                pass

        for idx, item in enumerate(items):
            cost_amount = _safe_float(item.get("cost_amount"))
            if cost_amount == 0:
                cost_amount = _safe_float(item.get("actual_amount"))
            if cost_amount == 0:
                cost_amount = _safe_float(item.get("estimated_amount"))

            unit_rate = _safe_float(item.get("unit_rate"))
            if unit_rate == 0:
                unit_rate = _safe_float(item.get("unit_price"))

            qty = _safe_float(item.get("qty"))
            if qty == 0:
                qty = _safe_float(item.get("quantity"))

            cost_date = item.get("cost_date") or item.get("date")
            cost_detail = item.get("cost_detail") or item.get("description") or item.get("name")
            pay_to = item.get("pay_to") or item.get("vendor")
            remarks = item.get("remarks") or item.get("notes")
            head_materials = item.get("cost_head_materials") or item.get("category_name")
            head_project = item.get("cost_head_project") or item.get("project_name")

            row_values = {
                "receive_date": _cell_date(item.get("receive_date")),
                "receive_detail": _text(item.get("receive_detail")),
                "receive_amount": _num_text(item.get("receive_amount")),
                "received_from": _text(item.get("received_from")),
                "cost_date": _cell_date(cost_date),
                "cost_detail": _text(cost_detail),
                "cost_amount": _num_text(cost_amount),
                "pay_to": _text(pay_to),
                "unit": _text(item.get("unit")),
                "unit_rate": _num_text(unit_rate),
                "qty": _num_text(qty),
                "qty_cft": _num_text(item.get("qty_cft")),
                "remarks": _text(remarks),
                "cost_head_materials": _text(head_materials),
                "structure_or_finishing": _text(item.get("structure_or_finishing")),
                "cost_summary_1": _text(item.get("cost_summary_1")),
                "category_boq_mapping": _text(item.get("category_boq_mapping")),
                "cost_head_floors": _text(item.get("cost_head_floors")),
                "cost_head_project": _text(head_project),
                "cost_head_months": _text(item.get("cost_head_months")),
            }

            values = [row_values[key] for key, _label, _w, _a in TRACKER_TABLE_COLUMNS]
            # Append extra values
            for ek in self._extra_column_keys:
                values.append(_text(item.get(ek)))
            self.tree.insert("", "end", iid=str(item["id"]), values=values, tags=("even" if idx % 2 == 0 else "odd",))

    def open_item_detail(self, item):
        dialog = ctk.CTkToplevel(self)
        dialog.title(item.get("name") or "Cost Item")
        dialog.geometry("680x700")
        dialog.configure(fg_color="#0f172a")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        title = (
            item.get("cost_detail")
            or item.get("receive_detail")
            or item.get("description")
            or item.get("name")
            or "Cost Item"
        )

        cost_amount = _safe_float(item.get("cost_amount"))
        if cost_amount == 0:
            cost_amount = _safe_float(item.get("actual_amount"))
        if cost_amount == 0:
            cost_amount = _safe_float(item.get("estimated_amount"))

        unit_rate = _safe_float(item.get("unit_rate"))
        if unit_rate == 0:
            unit_rate = _safe_float(item.get("unit_price"))

        qty = _safe_float(item.get("qty"))
        if qty == 0:
            qty = _safe_float(item.get("quantity"))

        cost_date = item.get("cost_date") or item.get("date")
        pay_to = item.get("pay_to") or item.get("vendor")
        remarks = item.get("remarks") or item.get("notes")
        head_materials = item.get("cost_head_materials") or item.get("category_name") or "Uncategorized"
        head_project = item.get("cost_head_project") or item.get("project_name") or "No project"

        ctk.CTkLabel(dialog, text=title, font=ctk.CTkFont(size=24, weight="bold"), text_color="white").pack(anchor="w", padx=28, pady=(24, 4))
        ctk.CTkLabel(dialog, text=f"{head_materials} | {head_project}", font=ctk.CTkFont(size=12), text_color="#94a3b8").pack(anchor="w", padx=28)

        body = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=(16, 10))
        
        card = ctk.CTkFrame(body, fg_color="#111827", corner_radius=16, border_width=1, border_color="#223356")
        card.pack(fill="x")
        
        fields = [
            ("Receive DATE", _date_text(item.get("receive_date"))),
            ("Receive DETAIL", _text(item.get("receive_detail")) or "-"),
            ("Receive AMOUNT", _money(item.get("receive_amount")) if _safe_float(item.get("receive_amount")) else "-"),
            ("RECEIVED FROM", _text(item.get("received_from")) or "-"),
            ("Cost DATE", _date_text(cost_date)),
            ("Cost DETAIL", _text(item.get("cost_detail")) or _text(item.get("description")) or _text(item.get("name")) or "-"),
            ("Cost AMOUNT", _money(cost_amount) if cost_amount else "-"),
            ("PAY TO", _text(pay_to) or "-"),
            ("Unit", _text(item.get("unit")) or "-"),
            ("Unit Rate", _money(unit_rate) if unit_rate else "-"),
            ("Qty", f"{qty:g}" if qty else "-"),
            ("Qty (CFT)", f"{_safe_float(item.get('qty_cft')):g}" if _safe_float(item.get("qty_cft")) else "-"),
            ("REMARKS", _text(remarks) or "-"),
            ("COST HEAD (Materials)", _text(head_materials) or "-"),
            ("Structure/Finishing", _text(item.get("structure_or_finishing")) or "-"),
            ("Cost Summary 1", _text(item.get("cost_summary_1")) or "-"),
            ("Category BOQ Mapping", _text(item.get("category_boq_mapping")) or "-"),
            ("COST HEAD (Floors)", _text(item.get("cost_head_floors")) or "-"),
            ("COST HEAD (Project & Office)", _text(head_project) or "-"),
            ("COST HEAD (Months)", _text(item.get("cost_head_months")) or "-"),
        ]

        # Add extra fields if they have data
        for i in range(1, 11):
            key = f"extra_{i}"
            val = _text(item.get(key))
            if val:
                label = self.extra_labels.get(key, key)
                fields.append((label, val))
            
        for label, value in fields:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=8)
            ctk.CTkLabel(row, text=label, width=180, anchor="w", font=ctk.CTkFont(size=12, weight="bold"), text_color="#9bb0d5").pack(side="left")
            ctk.CTkLabel(row, text=value, font=ctk.CTkFont(size=12), text_color="#f8fafc", wraplength=380, justify="left").pack(side="left", fill="x", expand=True)

        footer = ctk.CTkFrame(dialog, fg_color="transparent")
        footer.pack(fill="x", padx=24, pady=(0, 20))
        ctk.CTkButton(footer, text="Close", fg_color="#1e293b", hover_color="#334155", height=38, corner_radius=10, command=dialog.destroy).pack(side="left")
        ctk.CTkButton(footer, text="Edit Item", fg_color="#3b82f6", hover_color="#2563eb", height=38, corner_radius=10, command=lambda: [dialog.destroy(), self.open_edit_item(item)]).pack(side="right")
        ctk.CTkButton(footer, text="Delete Item", fg_color="#ef4444", hover_color="#dc2626", height=38, corner_radius=10, command=lambda: [dialog.destroy(), self.delete_item(item["id"])]).pack(side="right", padx=(0, 10))

    def open_add_item(self):
        self._open_item_dialog(None)

    def open_edit_item(self, item):
        self._open_item_dialog(item)

    def _open_item_dialog(self, item):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Edit Material / Cost Item" if item else "Add Material / Cost Item")
        dialog.geometry("720x900")
        dialog.configure(fg_color="#0f172a")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        ctk.CTkLabel(
            dialog,
            text="Edit Cost Row (Excel Template)" if item else "Add Cost Row (Excel Template)",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="white",
        ).pack(pady=(20, 10))
        form = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=30, pady=(0, 5))

        entries = {}
        combos = {}

        def add_entry(label, key, default="", placeholder="", *, height=34):
            ctk.CTkLabel(form, text=label, font=ctk.CTkFont(size=12, weight="bold"), text_color="#94a3b8").pack(anchor="w", pady=(8, 2))
            entry = ctk.CTkEntry(
                form,
                height=height,
                fg_color="#1e293b",
                border_color="#334155",
                corner_radius=8,
                placeholder_text=placeholder,
            )
            value = ""
            if item is not None:
                raw = item.get(key)
                if raw is not None:
                    value = str(raw)
            elif default:
                value = str(default)
            if value and value.lower() != "nan":
                entry.insert(0, value)
            entry.pack(fill="x")
            entries[key] = entry
            return entry

        class _SearchableDropdown(ctk.CTkFrame):
            def __init__(self, parent, values, default=""):
                super().__init__(parent, fg_color="transparent")
                self._values = [str(v) for v in (values or []) if v is not None]
                self._popup = None
                self._listbox = None

                self.entry = ctk.CTkEntry(
                    self,
                    height=34,
                    fg_color="#1e293b",
                    border_color="#334155",
                    corner_radius=8,
                )
                self.entry.pack(side="left", fill="x", expand=True)
                self.entry.bind("<KeyRelease>", self._on_type)
                self.entry.bind("<Down>", self._open_popup)

                self.button = ctk.CTkButton(
                    self,
                    text="v",
                    width=36,
                    height=34,
                    fg_color="#2a3547",
                    hover_color="#3a475d",
                    corner_radius=8,
                    command=self._toggle_popup,
                )
                self.button.pack(side="right", padx=(6, 0))

                if default:
                    self.set(default)

            def set(self, value: str):
                self.entry.delete(0, "end")
                self.entry.insert(0, str(value))

            def get(self) -> str:
                return self.entry.get()

            def _get_dialog(self):
                return self.winfo_toplevel()

            def _toggle_popup(self):
                if self._popup and self._popup.winfo_exists():
                    self._close_popup()
                    return
                self._open_popup()

            def _on_type(self, _event=None):
                if self._popup and self._popup.winfo_exists():
                    self._refresh_list()

            def _open_popup(self, _event=None):
                if self._popup and self._popup.winfo_exists():
                    return
                dialog = self._get_dialog()
                self._popup = tk.Toplevel(dialog)
                self._popup.wm_overrideredirect(True)
                self._popup.attributes("-topmost", True)
                self._popup.transient(dialog)

                # Position below the entry
                self.update_idletasks()
                x = self.entry.winfo_rootx()
                y = self.entry.winfo_rooty() + self.entry.winfo_height()
                width = self.entry.winfo_width() + self.button.winfo_width() + 6
                height = 220
                self._popup.geometry(f"{width}x{height}+{x}+{y}")

                frame = tk.Frame(self._popup, bg="#0f172a")
                frame.pack(fill="both", expand=True)

                self._listbox = tk.Listbox(
                    frame,
                    activestyle="none",
                    bg="#0f172a",
                    fg="#e2e8f0",
                    highlightthickness=0,
                    selectbackground="#1e293b",
                    selectforeground="#f8fafc",
                )
                self._listbox.pack(side="left", fill="both", expand=True)
                scrollbar = tk.Scrollbar(frame, orient="vertical", command=self._listbox.yview)
                scrollbar.pack(side="right", fill="y")
                self._listbox.configure(yscrollcommand=scrollbar.set)

                self._listbox.bind("<Double-Button-1>", self._choose_value)
                self._listbox.bind("<Return>", self._choose_value)
                self._listbox.bind("<Escape>", lambda _e: self._close_popup())
                self._popup.bind("<Escape>", lambda _e: self._close_popup())
                # Ensure the list scrolls instead of the main dialog.
                self._listbox.bind("<MouseWheel>", self._on_mousewheel)
                self._popup.bind("<MouseWheel>", self._on_mousewheel)

                self._refresh_list()
                self._listbox.focus_set()
                try:
                    self._popup.grab_set()
                except Exception:
                    pass

            def _refresh_list(self):
                if not self._listbox:
                    return
                self._listbox.delete(0, "end")
                needle = self.entry.get().strip().lower()
                values = [v for v in self._values if needle in v.lower()] if needle else self._values
                for value in values:
                    self._listbox.insert("end", value)

            def _on_mousewheel(self, event):
                if not self._listbox:
                    return "break"
                delta = -1 if event.delta > 0 else 1
                self._listbox.yview_scroll(delta, "units")
                return "break"

            def _choose_value(self, _event=None):
                if not self._listbox:
                    return
                selection = self._listbox.curselection()
                if not selection:
                    return
                value = self._listbox.get(selection[0])
                self.set(value)
                self._close_popup()

            def _close_popup(self):
                if self._popup and self._popup.winfo_exists():
                    try:
                        self._popup.grab_release()
                    except Exception:
                        pass
                    self._popup.destroy()
                self._popup = None
                dialog = self._get_dialog()
                try:
                    dialog.grab_set()
                except Exception:
                    pass

        def add_combo(label, key, values, default=""):
            ctk.CTkLabel(form, text=label, font=ctk.CTkFont(size=12, weight="bold"), text_color="#94a3b8").pack(anchor="w", pady=(8, 2))
            box = _SearchableDropdown(form, values, default=str(default or ""))
            box.pack(fill="x")
            combos[key] = box
            return box

        def distinct_values(column: str, limit: int = 400) -> list[str]:
            try:
                rows = execute_query(
                    f"SELECT DISTINCT `{column}` AS v FROM cost_items "
                    f"WHERE `{column}` IS NOT NULL AND TRIM(`{column}`) <> '' "
                    f"ORDER BY v LIMIT {int(limit)}"
                )
                return [str(r.get("v")) for r in (rows or []) if r.get("v") is not None]
            except Exception:
                return []

        ctk.CTkLabel(form, text="Project (Database)", font=ctk.CTkFont(size=14, weight="bold"), text_color="white").pack(anchor="w", pady=(6, 2))
        projects = execute_query("SELECT id, name FROM projects ORDER BY name") or []
        project_options = ["(No Project)"] + [f"{p['id']} | {p['name']}" for p in projects] + ["+ Create new project..."]
        project_var = ctk.StringVar(value="(No Project)")
        if item and item.get("project_id"):
            try:
                pid = int(item.get("project_id"))
                name = next((p.get("name") for p in projects if int(p.get("id")) == pid), None)
                if name:
                    project_var.set(f"{pid} | {name}")
            except Exception:
                pass
        project_menu = ctk.CTkOptionMenu(
            form,
            values=project_options,
            variable=project_var,
            fg_color="#1e293b",
            button_color="#334155",
            height=38,
        )
        project_menu.pack(fill="x")

        new_project_entry = ctk.CTkEntry(
            form,
            height=34,
            fg_color="#1e293b",
            border_color="#334155",
            corner_radius=8,
            placeholder_text="New project name (only if creating)",
        )

        def _sync_project_entry(*_):
            if project_var.get() == "+ Create new project...":
                new_project_entry.pack(fill="x", pady=(8, 0))
            else:
                try:
                    new_project_entry.pack_forget()
                except Exception:
                    pass

        project_var.trace_add("write", _sync_project_entry)
        _sync_project_entry()

        ctk.CTkLabel(form, text="\n--- Receive (Excel) ---", font=ctk.CTkFont(size=14, weight="bold"), text_color="white").pack(anchor="w", pady=(12, 2))
        add_entry("Receive DATE", "receive_date", placeholder="YYYY-MM-DD")
        add_entry("Receive DETAIL", "receive_detail", placeholder="e.g. Adjustment / Funding")
        add_entry("Receive AMOUNT", "receive_amount", placeholder="e.g. 250000")
        add_combo("RECEIVED FROM", "received_from", distinct_values("received_from"), default=(item.get("received_from") if item else ""))

        ctk.CTkLabel(form, text="\n--- Cost (Excel) ---", font=ctk.CTkFont(size=14, weight="bold"), text_color="white").pack(anchor="w", pady=(12, 2))
        add_entry("Cost DATE", "cost_date", default=datetime.now().strftime("%Y-%m-%d"), placeholder="YYYY-MM-DD")
        add_entry("Cost DETAIL", "cost_detail", placeholder="e.g. Cement purchase")
        add_entry("Cost AMOUNT", "cost_amount", placeholder="e.g. 5000")
        add_combo("PAY TO", "pay_to", distinct_values("pay_to"), default=(item.get("pay_to") if item else ""))

        ctk.CTkLabel(form, text="\n--- Units ---", font=ctk.CTkFont(size=14, weight="bold"), text_color="white").pack(anchor="w", pady=(12, 2))
        unit_values = list(dict.fromkeys(distinct_values("unit") + UNIT_OPTIONS))
        add_combo("Unit", "unit", unit_values, default=(item.get("unit") if item else (UNIT_OPTIONS[0] if UNIT_OPTIONS else "")))
        add_entry("Unit Rate", "unit_rate", placeholder="e.g. 120")
        add_entry("Qty", "qty", placeholder="e.g. 10")
        add_entry("Qty (CFT)", "qty_cft", placeholder="e.g. 32.5")

        ctk.CTkLabel(form, text="\n--- Classifications (Cost Heads) ---", font=ctk.CTkFont(size=14, weight="bold"), text_color="white").pack(anchor="w", pady=(12, 2))
        add_combo("COST HEAD (Materials)", "cost_head_materials", distinct_values("cost_head_materials"), default=(item.get("cost_head_materials") if item else ""))
        add_combo("Structure/Finishing", "structure_or_finishing", distinct_values("structure_or_finishing"), default=(item.get("structure_or_finishing") if item else ""))
        add_combo("Cost Summary 1", "cost_summary_1", distinct_values("cost_summary_1"), default=(item.get("cost_summary_1") if item else ""))
        add_combo("Category BOQ Mapping", "category_boq_mapping", distinct_values("category_boq_mapping"), default=(item.get("category_boq_mapping") if item else ""))
        add_combo("COST HEAD (Floors)", "cost_head_floors", distinct_values("cost_head_floors"), default=(item.get("cost_head_floors") if item else ""))
        add_combo("COST HEAD (Project & Office)", "cost_head_project", distinct_values("cost_head_project"), default=(item.get("cost_head_project") if item else ""))
        add_combo("COST HEAD (Months)", "cost_head_months", distinct_values("cost_head_months"), default=(item.get("cost_head_months") if item else ""))

        ctk.CTkLabel(form, text="\n--- REMARKS ---", font=ctk.CTkFont(size=14, weight="bold"), text_color="white").pack(anchor="w", pady=(12, 2))

        # --- Dynamic Extra Fields ---
        extra_entries = {}
        active_extras = [f"extra_{i}" for i in range(1, 11) if f"extra_{i}" in self.extra_labels]
        if active_extras or (item and any(item.get(f"extra_{i}") for i in range(1, 11))):
            ctk.CTkLabel(form, text="\n--- Extra Fields ---", font=ctk.CTkFont(size=14, weight="bold"), text_color="#f59e0b").pack(anchor="w", pady=(12, 2))
            for i in range(1, 11):
                key = f"extra_{i}"
                label = self.extra_labels.get(key)
                val = item.get(key) if item else None
                # Show field if it has a label OR if the item already has data for it
                if label or (val and str(val).strip()):
                    display_label = label or key
                    add_entry(display_label, key, placeholder=f"Extra field {i}")
        remarks_box = ctk.CTkTextbox(
            form,
            height=100,
            fg_color="#1e293b",
            border_color="#334155",
            border_width=1,
            corner_radius=8,
            wrap="word",
        )
        if item and item.get("remarks"):
            remarks_box.insert("1.0", str(item.get("remarks") or ""))
        remarks_box.pack(fill="x")

        def save():
            def _clean_text(value: str) -> str | None:
                text = (value or "").strip()
                return text or None

            def _clean_date(value: str) -> str | None:
                text = (value or "").strip()
                if not text:
                    return None
                if " " in text:
                    text = text.split(" ", 1)[0]
                return text

            def _clean_float(value: str) -> float:
                text = (value or "").strip().replace(",", "")
                if not text:
                    return 0.0
                try:
                    return float(text)
                except ValueError:
                    return 0.0

            receive_detail = _clean_text(entries["receive_detail"].get())
            cost_detail = _clean_text(entries["cost_detail"].get())
            if not receive_detail and not cost_detail:
                messagebox.showwarning("Validation", "Enter at least Receive DETAIL or Cost DETAIL.")
                return

            receive_amount = _clean_float(entries["receive_amount"].get())
            cost_amount = _clean_float(entries["cost_amount"].get())
            qty = _clean_float(entries["qty"].get())
            unit_rate = _clean_float(entries["unit_rate"].get())

            if cost_amount == 0 and qty > 0 and unit_rate > 0:
                cost_amount = qty * unit_rate

            project_id = None
            if project_var.get() == "+ Create new project...":
                name = (new_project_entry.get() or "").strip()
                if not name:
                    messagebox.showwarning("Validation", "Enter a project name to create.")
                    return
                project_id = execute_query(
                    "INSERT INTO projects (name, created_by, created_at, updated_at) VALUES (%s, %s, NOW(), NOW())",
                    (name, self.user.get("id")),
                    fetch=False,
                )
                # refresh local projects dropdowns
                try:
                    self.load_categories()
                except Exception:
                    pass
            elif project_var.get() != "(No Project)":
                try:
                    project_id = int(str(project_var.get()).split("|", 1)[0].strip())
                except Exception:
                    project_id = None

            payload = (
                project_id,
                _clean_date(entries["receive_date"].get()),
                receive_detail,
                receive_amount,
                _clean_text(combos["received_from"].get()),
                _clean_date(entries["cost_date"].get()),
                cost_detail,
                cost_amount,
                _clean_text(combos["pay_to"].get()),
                _clean_text(combos["unit"].get()),
                unit_rate,
                qty,
                _clean_float(entries["qty_cft"].get()),
                _clean_text(remarks_box.get("1.0", "end").strip()),
                _clean_text(combos["cost_head_materials"].get()),
                _clean_text(combos["structure_or_finishing"].get()),
                _clean_text(combos["cost_summary_1"].get()),
                _clean_text(combos["category_boq_mapping"].get()),
                _clean_text(combos["cost_head_floors"].get()),
                _clean_text(combos["cost_head_project"].get()),
                _clean_text(combos["cost_head_months"].get()),
            )

            # Collect extra field values
            extra_vals = tuple(
                _clean_text(entries[f"extra_{i}"].get()) if f"extra_{i}" in entries else None
                for i in range(1, 11)
            )
            try:
                if item:
                    execute_query(
                        """
                        UPDATE cost_items SET
                            project_id=%s,
                            receive_date=%s, receive_detail=%s, receive_amount=%s, received_from=%s,
                            cost_date=%s, cost_detail=%s, cost_amount=%s, pay_to=%s,
                            unit=%s, unit_rate=%s, qty=%s, qty_cft=%s, remarks=%s,
                            cost_head_materials=%s, structure_or_finishing=%s, cost_summary_1=%s,
                            category_boq_mapping=%s, cost_head_floors=%s, cost_head_project=%s, cost_head_months=%s,
                            extra_1=%s, extra_2=%s, extra_3=%s, extra_4=%s, extra_5=%s,
                            extra_6=%s, extra_7=%s, extra_8=%s, extra_9=%s, extra_10=%s,
                            updated_at=NOW()
                        WHERE id=%s
                        """, 
                        payload + extra_vals + (item["id"],), 
                        fetch=False
                    )
                else:
                    execute_query(
                        """
                        INSERT INTO cost_items (
                            project_id,
                            receive_date, receive_detail, receive_amount, received_from,
                            cost_date, cost_detail, cost_amount, pay_to,
                            unit, unit_rate, qty, qty_cft, remarks,
                            cost_head_materials, structure_or_finishing, cost_summary_1,
                            category_boq_mapping, cost_head_floors, cost_head_project, cost_head_months,
                            extra_1, extra_2, extra_3, extra_4, extra_5,
                            extra_6, extra_7, extra_8, extra_9, extra_10,
                            created_by, created_at, updated_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                        """, 
                        payload + extra_vals + (self.user.get("id"),), 
                        fetch=False
                    )
            except Exception as exc:
                messagebox.showerror("Error", str(exc))
                return
            dialog.destroy()
            self.load_items()
            try:
                self.load_categories()
            except Exception:
                pass

        footer = ctk.CTkFrame(dialog, fg_color="transparent")
        footer.pack(fill="x", padx=30, pady=(5, 20))
        ctk.CTkButton(footer, text="Cancel", fg_color="#1e293b", hover_color="#334155", height=38, command=dialog.destroy).pack(side="left")
        ctk.CTkButton(footer, text="Save", fg_color="#3b82f6", hover_color="#2563eb", height=38, command=save).pack(side="right")

    def delete_item(self, item_id):
        if not messagebox.askyesno("Confirm", "Delete this cost item? It will be moved to Recycle Bin."):
            return
        try:
            recycle_and_delete(
                "cost_items",
                int(item_id),
                deleted_by=self.user.get("id"),
                reason="Deleted from Cost Management",
            )
            self.load_items()
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def delete_selected_items(self):
        selected = [int(i) for i in self.tree.selection() if str(i).isdigit()]
        if not selected:
            messagebox.showinfo("No Selection", "Select one or more rows first.")
            return
        if not messagebox.askyesno(
            "Confirm Bulk Delete",
            f"Delete {len(selected)} selected cost items?\n\nThey will be moved to Recycle Bin.",
        ):
            return
        try:
            recycle_and_delete_many(
                "cost_items",
                selected,
                deleted_by=self.user.get("id"),
                reason="Bulk delete from Cost Management",
            )
            self.load_items()
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def show_cost_heads(self):
        dialog.grab_set()

        self.cost_heads_search_var = ctk.StringVar()
        self.cost_heads_search_var.trace_add("write", lambda *args: self._update_cost_heads_ui(scroll_container))

        top_bar = ctk.CTkFrame(dialog, fg_color="transparent")
        top_bar.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(top_bar, text="Cost Heads", font=ctk.CTkFont(size=20, weight="bold"), text_color="white").pack(side="left")
        
        search_frame = ctk.CTkFrame(top_bar, fg_color="#1e293b", height=36, corner_radius=8)
        search_frame.pack(side="right", fill="x", expand=True, padx=(20, 0))
        
        ctk.CTkLabel(search_frame, text="🔍", font=ctk.CTkFont(size=14)).pack(side="left", padx=10)
        self.ch_search_entry = ctk.CTkEntry(search_frame, placeholder_text="Search cost heads...", 
                                           textvariable=self.cost_heads_search_var,
                                           fg_color="transparent", border_width=0, height=30)
        self.ch_search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkLabel(
            dialog,
            text="Click a cost head to view detailed transactions and materials.",
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8",
        ).pack(anchor="w", padx=22, pady=(0, 10))

        scroll_container = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        scroll_container.pack(fill="both", expand=True, padx=18, pady=(0, 18))
        
        self._update_cost_heads_ui(scroll_container)

    def _update_cost_heads_ui(self, container):
        for w in container.winfo_children():
            w.destroy()

        search_term = self.cost_heads_search_var.get().lower()
        
        columns = [
            ("COST HEAD (Materials)", "cost_head_materials"),
            ("Structure/Finishing", "structure_or_finishing"),
            ("Cost Summary 1", "cost_summary_1"),
            ("Category BOQ Mapping", "category_boq_mapping"),
            ("COST HEAD (Floors)", "cost_head_floors"),
            ("COST HEAD (Project & Office)", "cost_head_project"),
            ("COST HEAD (Months)", "cost_head_months"),
        ]

        for title, col in columns:
            try:
                rows = execute_query(
                    f"SELECT {col} AS value, COUNT(*) AS cnt "
                    f"FROM cost_items "
                    f"WHERE {col} IS NOT NULL AND TRIM({col}) <> '' "
                    f"GROUP BY {col} "
                    f"ORDER BY cnt DESC, value ASC"
                )
            except Exception:
                continue

            # Filter rows based on search
            filtered_rows = [r for r in (rows or []) if search_term in str(r['value']).lower()]
            if not filtered_rows and search_term:
                continue

            card = ctk.CTkFrame(container, fg_color="#111827", corner_radius=12, border_width=1, border_color="#223356")
            card.pack(fill="x", pady=8)
            ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=14, weight="bold"), text_color="#3b82f6").pack(anchor="w", padx=14, pady=(12, 6))

            list_frame = ctk.CTkFrame(card, fg_color="#0f172a", corner_radius=10)
            list_frame.pack(fill="x", padx=10, pady=(0, 10))

            if not filtered_rows:
                ctk.CTkLabel(list_frame, text="(No matching values)", text_color="#475569").pack(pady=10)
                continue

            for row in filtered_rows:
                val = row['value']
                cnt = row['cnt']
                
                btn = ctk.CTkButton(
                    list_frame, 
                    text=f"{val} ({cnt})",
                    font=ctk.CTkFont(size=12),
                    fg_color="transparent",
                    hover_color="#1e293b",
                    anchor="w",
                    height=30,
                    text_color="#cbd5e1",
                    command=lambda c=col, v=val: self._show_filtered_costs(c, v)
                )
                btn.pack(fill="x", padx=5, pady=1)

    def _show_filtered_costs(self, column, value):
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Transactions: {value}")
        dialog.geometry("900x600")
        dialog.configure(fg_color="#0f172a")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        ctk.CTkLabel(dialog, text=f"Cost Transactions for '{value}'", font=ctk.CTkFont(size=18, weight="bold"), text_color="white").pack(pady=20)
        
        from tkinter import ttk
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Filtered.Treeview", background="#111827", foreground="white", fieldbackground="#111827", borderwidth=0, rowheight=30)
        style.map("Filtered.Treeview", background=[('selected', '#3b82f6')])
        
        table_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        cols = ("id", "date", "detail", "amount", "pay_to", "invoice")
        tree = ttk.Treeview(table_frame, columns=cols, show="headings", style="Filtered.Treeview")
        
        tree.heading("id", text="Trx #")
        tree.heading("date", text="Date")
        tree.heading("detail", text="Detail")
        tree.heading("amount", text="Amount")
        tree.heading("pay_to", text="Pay To")
        tree.heading("invoice", text="Invoice")
        
        tree.column("id", width=60)
        tree.column("date", width=100)
        tree.column("detail", width=300)
        tree.column("amount", width=100, anchor="e")
        tree.column("pay_to", width=150)
        tree.column("invoice", width=100)
        
        scrollbar = ctk.CTkScrollbar(table_frame, orientation="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        try:
            items = execute_query(
                f"SELECT id, cost_date, cost_detail, cost_amount, pay_to, invoice_no "
                f"FROM cost_items WHERE {column} = %s ORDER BY cost_date DESC",
                (value,)
            )
            for it in items:
                tree.insert("", "end", values=(
                    it['id'], 
                    it['cost_date'] or '-', 
                    it['cost_detail'] or '-', 
                    f"{float(it['cost_amount'] or 0):,.2f}", 
                    it['pay_to'] or '-',
                    it['invoice_no'] or '-'
                ))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load transactions: {e}")

        def open_item():
            sel = tree.selection()
            if not sel: return
            item_id = tree.item(sel[0])['values'][0]
            # Find item in database
            it = execute_query("SELECT * FROM cost_items WHERE id=%s", (item_id,))[0]
            self.open_item_detail(it)

        ctk.CTkButton(dialog, text="View Detailed Info", command=open_item, fg_color="#3b82f6").pack(pady=10)


    def show_categories(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Cost Categories")
        dialog.geometry("600x600")
        dialog.configure(fg_color="#0f172a")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Cost Categories", font=ctk.CTkFont(size=20, weight="bold"), text_color="white").pack(pady=(20, 15))
        scroll = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        try:
            categories = execute_query("SELECT * FROM cost_categories ORDER BY sort_order, name")
            for category in categories:
                row = ctk.CTkFrame(scroll, fg_color="#111827", corner_radius=8)
                row.pack(fill="x", pady=3)
                ctk.CTkLabel(row, text=category.get("icon") or "CAT", font=ctk.CTkFont(size=18, weight="bold"), width=48).pack(side="left", padx=(12, 5), pady=8)
                info = ctk.CTkFrame(row, fg_color="transparent")
                info.pack(side="left", fill="x", expand=True, padx=5)
                ctk.CTkLabel(info, text=category["name"], font=ctk.CTkFont(size=13, weight="bold"), text_color="#e2e8f0", anchor="w").pack(anchor="w")
                if category.get("description"):
                    ctk.CTkLabel(info, text=category["description"], font=ctk.CTkFont(size=11), text_color="#64748b", anchor="w", wraplength=400).pack(anchor="w")
                if category.get("is_default"):
                    ctk.CTkLabel(row, text="Default", font=ctk.CTkFont(size=10, weight="bold"), text_color="#3b82f6").pack(side="right", padx=12)
        except Exception as exc:
            ctk.CTkLabel(scroll, text=f"Error: {exc}", text_color="#ef4444").pack(pady=20)
