"""
Projects view for the desktop app.
Adds richer project listing fields and a property-style showcase dialog.
"""

import os
import sys
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk

try:
    from PIL import Image
except ImportError:
    Image = None

from core.database import ensure_project_profile_columns, execute_query
from core.projects_media import create_dummy_cover, pillow_available, resolve_image_path, store_project_image
from core.projects_service import (
    bulk_delete_projects,
    delete_project as delete_project_service,
    fetch_project,
    fetch_projects,
    project_metrics,
    project_snapshot,
)
from views.projects_layout import ProjectsLayout
from views.projects_shared import (
    BALCONY_OPTIONS,
    BATHROOM_OPTIONS,
    BEDROOM_OPTIONS,
    CONSTRUCTION_OPTIONS,
    DETAIL_FIELDS,
    FLOOR_RANGE_OPTIONS,
    GARAGE_OPTIONS,
    LISTING_OPTIONS,
    STATUS_COLORS,
    TOTAL_UNIT_OPTIONS,
    TRANSACTION_OPTIONS,
    TYPE_OPTIONS,
    display,
    format_currency,
    format_date,
    humanize,
    safe_float,
    safe_int,
    split_items,
    validate_date,
)


if getattr(sys, "frozen", False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class ProjectsView(ctk.CTkFrame):
    def __init__(self, parent, user):
        super().__init__(parent, fg_color="transparent")
        ensure_project_profile_columns()
        self.user = user
        self.projects = []
        self.layout = None

        self.build_ui()
        self.load_data()

    def build_ui(self):
        self.layout = ProjectsLayout(
            self,
            on_new=self.open_add_dialog,
            on_auto_covers=self.generate_dummy_covers,
            on_bulk_delete=self.open_bulk_delete,
            on_filters_change=self.load_data,
        )

    def load_data(self):
        self.layout.clear_cards()
        try:
            self.projects = fetch_projects(
                search=self.layout.search_var.get().strip(),
                status=self.layout.status_var.get(),
                purpose=self.layout.purpose_var.get(),
            )
        except Exception as exc:
            self.layout.show_error(f"Error loading projects: {exc}")
            return
        metrics = project_metrics(self.projects)
        self.layout.set_metrics(metrics)

        if not self.projects:
            self.layout.show_empty()
            return

        self.layout.render_projects(self.projects, self.open_project_detail, self.open_edit_dialog, self.delete_project)

    def generate_dummy_covers(self):
        if not pillow_available():
            messagebox.showwarning("Missing Dependency", "Pillow is required to generate demo cover images.")
            return

        try:
            projects = execute_query("SELECT id, name, location, property_type, cover_image_path FROM projects ORDER BY id ASC") or []
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
            return

        created = 0
        for project in projects:
            # Skip if a valid cover is already present.
            existing = resolve_image_path(project.get("cover_image_path"), APP_DIR)
            if existing:
                continue

            rel_path = create_dummy_cover(project, APP_DIR)
            if not rel_path:
                continue

            try:
                execute_query(
                    "UPDATE projects SET cover_image_path=%s, updated_at=NOW() WHERE id=%s",
                    (rel_path, int(project.get("id"))),
                    fetch=False,
                )
                created += 1
            except Exception:
                pass

        if created:
            self.load_data()
            messagebox.showinfo("Done", f"Generated {created} project cover images.")
        else:
            messagebox.showinfo("No Changes", "No missing covers found (or covers could not be created).")

    def open_bulk_delete(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Bulk Delete Projects")
        dialog.geometry("980x680")
        dialog.configure(fg_color="#0f172a")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        ctk.CTkLabel(
            dialog,
            text="Bulk Delete Projects",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#f8fafc",
        ).pack(anchor="w", padx=24, pady=(22, 4))
        ctk.CTkLabel(
            dialog,
            text="Select one or more projects to delete. Linked records will be moved to Recycle Bin first.",
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8",
        ).pack(anchor="w", padx=24, pady=(0, 12))

        wrap = ctk.CTkFrame(dialog, fg_color="#111827", corner_radius=14, border_width=1, border_color="#223356")
        wrap.pack(fill="both", expand=True, padx=20, pady=(0, 14))
        wrap.grid_columnconfigure(0, weight=1)
        wrap.grid_rowconfigure(0, weight=1)

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure(
            "Projects.Treeview",
            background="#111827",
            fieldbackground="#111827",
            foreground="#e2e8f0",
            rowheight=28,
            borderwidth=0,
            relief="flat",
        )
        style.map(
            "Projects.Treeview",
            background=[("selected", "#1e293b")],
            foreground=[("selected", "#f8fafc")],
        )
        style.configure(
            "Projects.Treeview.Heading",
            background="#0f172a",
            foreground="#94a3b8",
            relief="flat",
            font=("Segoe UI", 9, "bold"),
        )

        cols = ["id", "name", "location", "status", "budget"]
        tree = ttk.Treeview(wrap, columns=cols, show="headings", style="Projects.Treeview", selectmode="extended")
        headings = [
            ("id", "ID", 70, "e"),
            ("name", "PROJECT", 320, "w"),
            ("location", "LOCATION", 220, "w"),
            ("status", "STATUS", 120, "w"),
            ("budget", "BUDGET", 140, "e"),
        ]
        for key, label, width, anchor in headings:
            tree.heading(key, text=label, anchor=anchor)
            tree.column(key, width=width, anchor=anchor, stretch=key in {"name", "location"})

        v_scroll = ttk.Scrollbar(wrap, orient="vertical", command=tree.yview)
        h_scroll = ttk.Scrollbar(wrap, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        tree.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=(10, 0))
        v_scroll.grid(row=0, column=1, sticky="ns", padx=(0, 10), pady=(10, 0))
        h_scroll.grid(row=1, column=0, sticky="ew", padx=(10, 0), pady=(0, 10))

        try:
            rows = execute_query("SELECT id, name, location, status, total_budget FROM projects ORDER BY created_at DESC, id DESC") or []
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
            dialog.destroy()
            return

        for idx, row in enumerate(rows):
            pid = int(row.get("id"))
            values = [
                pid,
                row.get("name") or "",
                row.get("location") or "",
                humanize(row.get("status") or ""),
                format_currency(row.get("total_budget")),
            ]
            tree.insert("", "end", iid=str(pid), values=values, tags=("even" if idx % 2 == 0 else "odd",))

        def delete_selected():
            selected = [int(i) for i in tree.selection() if str(i).isdigit()]
            if not selected:
                messagebox.showinfo("No Selection", "Select one or more projects first.")
                return
            if not messagebox.askyesno(
                "Confirm Bulk Delete",
                f"Delete {len(selected)} projects?\n\nThey and linked rows will be moved to Recycle Bin.",
            ):
                return
            try:
                bulk_delete_projects(selected, deleted_by=self.user.get("id"))
            except Exception as exc:
                messagebox.showerror("Error", str(exc))
                return
            dialog.destroy()
            self.load_data()

        footer = ctk.CTkFrame(dialog, fg_color="transparent")
        footer.pack(fill="x", padx=20, pady=(0, 20))
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
            text="Delete Selected",
            fg_color="#ef4444",
            hover_color="#dc2626",
            corner_radius=10,
            height=38,
            command=delete_selected,
        ).pack(side="right")

    def _bulk_delete_projects(self, project_ids):
        bulk_delete_projects(project_ids, deleted_by=self.user.get("id"))

    def open_add_dialog(self):
        self._open_dialog(None)

    def open_edit_dialog(self, project):
        self._open_dialog(project)

    def open_project_detail(self, project):
        project = fetch_project(project["id"])
        if not project:
            messagebox.showwarning("Missing Project", "This project could not be loaded.")
            self.load_data()
            return

        try:
            snapshot = project_snapshot(project["id"], project.get("name"))
            investments = snapshot["investments"]
            collections = snapshot["collections"]
            costs = snapshot["costs"]
            contractors = snapshot["contractors"]
        except Exception:
            investments = collections = costs = contractors = 0
        net = safe_float(investments) + safe_float(collections) - safe_float(costs) - safe_float(contractors)

        dialog = ctk.CTkToplevel(self)
        dialog.title(project.get("name") or "Project Detail")
        dialog.geometry("1380x900")
        dialog.minsize(1180, 780)
        dialog.configure(fg_color="#08111f")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        scroll = ctk.CTkScrollableFrame(dialog, fg_color="transparent", scrollbar_button_color="#1c2b48", scrollbar_button_hover_color="#27406b")
        scroll.pack(fill="both", expand=True, padx=18, pady=(18, 10))

        hero = ctk.CTkFrame(scroll, fg_color="#0b1327", corner_radius=26, border_width=1, border_color="#1e2d49")
        hero.pack(fill="x", pady=(0, 16))
        top = ctk.CTkFrame(hero, fg_color="transparent")
        top.pack(fill="x", padx=24, pady=(22, 12))
        title = ctk.CTkFrame(top, fg_color="transparent")
        title.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(title, text=display(project.get("name")), font=ctk.CTkFont(size=30, weight="bold"), text_color="#f8fafc").pack(anchor="w")
        ctk.CTkLabel(title, text=display(project.get("location"), "Location pending"), font=ctk.CTkFont(size=13), text_color="#8ea3c7").pack(anchor="w", pady=(4, 0))
        badge_col = ctk.CTkFrame(top, fg_color="transparent")
        badge_col.pack(side="right")
        ctk.CTkLabel(badge_col, text=display(project.get("property_for"), "Listing").upper(), font=ctk.CTkFont(size=11, weight="bold"), text_color="#08111f", fg_color="#f6c85f", corner_radius=10, padx=12, pady=6).pack(anchor="e")
        ctk.CTkLabel(badge_col, text=humanize(project.get("status") or "planning"), font=ctk.CTkFont(size=11, weight="bold"), text_color="#f8fafc", fg_color=STATUS_COLORS.get(str(project.get("status") or "planning").lower(), "#4b5563"), corner_radius=10, padx=12, pady=6).pack(anchor="e", pady=(8, 0))

        body = ctk.CTkFrame(hero, fg_color="transparent")
        body.pack(fill="x", padx=24, pady=(0, 24))
        body.grid_columnconfigure(0, weight=11)
        body.grid_columnconfigure(1, weight=9)
        visual = ctk.CTkFrame(body, fg_color="#0d1630", corner_radius=24, border_width=1, border_color="#223356", height=380)
        visual.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        visual.pack_propagate(False)

        image_path = resolve_image_path(project.get("cover_image_path"), APP_DIR)
        if image_path and Image is not None:
            try:
                cover = ctk.CTkImage(Image.open(image_path), size=(700, 380))
                dialog._project_cover = cover
                ctk.CTkLabel(visual, text="", image=cover).pack(fill="both", expand=True, padx=10, pady=10)
            except Exception:
                image_path = None
        if not image_path or Image is None:
            inner = ctk.CTkFrame(visual, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=24, pady=24)
            initials = "".join(part[:1] for part in str(project.get("name") or "P").split()[:2]).upper() or "P"
            ctk.CTkLabel(inner, text=display(project.get("property_type") or humanize(project.get("type")), "Residential Tower").upper(), font=ctk.CTkFont(size=11, weight="bold"), text_color="#8ea3c7").pack(anchor="w")
            badge = ctk.CTkFrame(inner, fg_color="#4f8cff", width=96, height=96, corner_radius=28)
            badge.pack(anchor="w", pady=(18, 16))
            badge.pack_propagate(False)
            ctk.CTkLabel(badge, text=initials, font=ctk.CTkFont(size=34, weight="bold"), text_color="#f8fafc").pack(expand=True)
            ctk.CTkLabel(inner, text=display(project.get("name")), font=ctk.CTkFont(size=30, weight="bold"), text_color="#f8fafc", wraplength=560, justify="left").pack(anchor="w")
            ctk.CTkLabel(inner, text=display(project.get("description"), "Add a cover image path to show a hero photo, or keep this rich placeholder layout for the desktop showcase."), font=ctk.CTkFont(size=13), text_color="#c7d5f2", wraplength=560, justify="left").pack(anchor="w", pady=(12, 0))

        glance = ctk.CTkFrame(body, fg_color="#101b35", corner_radius=24, border_width=1, border_color="#233154")
        glance.grid(row=0, column=1, sticky="nsew")
        ctk.CTkLabel(glance, text="AT A GLANCE", font=ctk.CTkFont(size=22, weight="bold"), text_color="#f8fafc").pack(anchor="w", padx=22, pady=(18, 12))
        ctk.CTkFrame(glance, fg_color="#223356", height=1).pack(fill="x", padx=22)
        for label, key in DETAIL_FIELDS:
            value = format_date(project.get(key)) if key in {"start_date", "estimated_end_date"} else display(project.get(key), "TBD")
            row = ctk.CTkFrame(glance, fg_color="transparent")
            row.pack(fill="x", padx=22, pady=8)
            ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=12, weight="bold"), text_color="#9bb0d5", width=170, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=value, font=ctk.CTkFont(size=12), text_color="#f8fafc", justify="right", wraplength=320).pack(side="right", fill="x", expand=True)
            ctk.CTkFrame(glance, fg_color="#162642", height=1).pack(fill="x", padx=22)

        summary = ctk.CTkFrame(scroll, fg_color="transparent")
        summary.pack(fill="x", pady=(0, 14))
        for idx in range(5):
            summary.grid_columnconfigure(idx, weight=1)
        for col_idx, label, value, color in [
            (0, "Location", display(project.get("location"), "TBD"), "#9bb0d5"),
            (1, "Apartment Size", display(project.get("unit_size") or project.get("building_area"), "TBD"), "#f8fafc"),
            (2, "Bedroom", display(project.get("bedrooms"), "TBD"), "#f8fafc"),
            (3, "Expected Completion", format_date(project.get("estimated_end_date")), "#f8fafc"),
            (4, "Status", display(project.get("construction_status") or humanize(project.get("status")), "TBD"), "#27d3a2"),
        ]:
            card = ctk.CTkFrame(summary, fg_color="#111d39", corner_radius=16, border_width=1, border_color="#233154", height=88)
            card.grid(row=0, column=col_idx, sticky="nsew", padx=5, pady=4)
            card.pack_propagate(False)
            ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=11), text_color="#7184aa").pack(anchor="w", padx=16, pady=(14, 0))
            ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=16, weight="bold"), text_color=color, wraplength=200, justify="left").pack(anchor="w", padx=16, pady=(6, 0))

        finance = ctk.CTkFrame(scroll, fg_color="#0d1630", corner_radius=22, border_width=1, border_color="#1f2a45")
        finance.pack(fill="x", pady=(0, 14))
        ctk.CTkLabel(finance, text="Portfolio Snapshot", font=ctk.CTkFont(size=22, weight="bold"), text_color="#f8fafc").pack(anchor="w", padx=22, pady=(18, 10))
        grid = ctk.CTkFrame(finance, fg_color="transparent")
        grid.pack(fill="x", padx=18, pady=(0, 16))
        for idx in range(5):
            grid.grid_columnconfigure(idx, weight=1)
        for col_idx, label, value, color in [
            (0, "Confirmed Investments", investments, "#27d3a2"),
            (1, "Collected From Schedules", collections, "#4f8cff"),
            (2, "Cost Items Posted", costs, "#ffb347"),
            (3, "Contractor Payments", contractors, "#ff7a90"),
            (4, "Net Position", net, "#f6c85f"),
        ]:
            card = ctk.CTkFrame(grid, fg_color="#111d39", corner_radius=16, border_width=1, border_color="#233154", height=86)
            card.grid(row=0, column=col_idx, sticky="nsew", padx=4, pady=4)
            card.pack_propagate(False)
            ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=11), text_color="#7184aa").pack(anchor="w", padx=14, pady=(14, 0))
            ctk.CTkLabel(card, text=format_currency(value), font=ctk.CTkFont(size=16, weight="bold"), text_color=color).pack(anchor="w", padx=14, pady=(6, 0))

        content = ctk.CTkFrame(scroll, fg_color="transparent")
        content.pack(fill="x", pady=(0, 14))
        content.grid_columnconfigure(0, weight=11)
        content.grid_columnconfigure(1, weight=9)
        self._text_card(content, 0, "Property Description", project.get("description"), 230, (0, 7))
        self._features_card(content, 1, project.get("features"), (7, 0))

        bottom = ctk.CTkFrame(scroll, fg_color="transparent")
        bottom.pack(fill="x", pady=(0, 10))
        bottom.grid_columnconfigure(0, weight=1)
        bottom.grid_columnconfigure(1, weight=1)
        self._text_card(bottom, 0, "Nearby Highlights", project.get("nearby_places"), 220, (0, 7))
        self._text_card(bottom, 1, "Corporate Office / Sales Note", project.get("corporate_office"), 220, (7, 0))

        footer = ctk.CTkFrame(dialog, fg_color="transparent")
        footer.pack(fill="x", padx=18, pady=(0, 18))
        ctk.CTkButton(footer, text="Close", width=88, height=38, corner_radius=10, fg_color="#182748", hover_color="#223660", command=dialog.destroy).pack(side="right")
        ctk.CTkButton(footer, text="Edit Project", height=38, corner_radius=10, fg_color="#4f8cff", hover_color="#3578f6", command=lambda: [dialog.destroy(), self.open_edit_dialog(project)]).pack(side="right", padx=(0, 8))

    def _text_card(self, parent, column, title, text, height, pad):
        card = ctk.CTkFrame(parent, fg_color="#0d1630", corner_radius=22, border_width=1, border_color="#1f2a45")
        card.grid(row=0, column=column, sticky="nsew", padx=pad, pady=4)
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=22, weight="bold"), text_color="#f8fafc").pack(anchor="w", padx=22, pady=(18, 12))
        box = ctk.CTkTextbox(card, fg_color="#111d39", border_color="#233154", border_width=1, corner_radius=16, wrap="word", font=ctk.CTkFont(size=13), text_color="#d9e6ff", height=height)
        box.pack(fill="both", expand=True, padx=18, pady=(0, 18))
        box.insert("1.0", display(text))
        box.configure(state="disabled")

    def _features_card(self, parent, column, value, pad):
        card = ctk.CTkFrame(parent, fg_color="#0d1630", corner_radius=22, border_width=1, border_color="#1f2a45")
        card.grid(row=0, column=column, sticky="nsew", padx=pad, pady=4)
        ctk.CTkLabel(card, text="Property Features", font=ctk.CTkFont(size=22, weight="bold"), text_color="#f8fafc").pack(anchor="w", padx=22, pady=(18, 12))
        items = split_items(value)
        if not items:
            ctk.CTkLabel(card, text="No features added yet. Use the edit form to list amenities like lift, CCTV, generator, and fire protection.", font=ctk.CTkFont(size=13), text_color="#8ea3c7", wraplength=420, justify="left").pack(anchor="w", padx=22, pady=(0, 20))
            return
        grid = ctk.CTkFrame(card, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=18, pady=(0, 18))
        for idx in range(3):
            grid.grid_columnconfigure(idx, weight=1)
        for idx, item in enumerate(items):
            chip = ctk.CTkFrame(grid, fg_color="#111d39", corner_radius=14, border_width=1, border_color="#233154", height=54)
            chip.grid(row=idx // 3, column=idx % 3, sticky="ew", padx=4, pady=4)
            chip.pack_propagate(False)
            ctk.CTkLabel(chip, text=item, font=ctk.CTkFont(size=12, weight="bold"), text_color="#d8e4ff", wraplength=140, justify="center").pack(expand=True, padx=10, pady=8)

    def _open_dialog(self, project):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Edit Project" if project else "New Project")
        dialog.geometry("760x900")
        dialog.minsize(680, 760)
        dialog.configure(fg_color="#08111f")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Edit Project" if project else "New Project", font=ctk.CTkFont(size=24, weight="bold"), text_color="#f8fafc").pack(anchor="w", padx=28, pady=(22, 6))
        ctk.CTkLabel(dialog, text="Fill both operational project fields and listing-style property details for the desktop showcase.", font=ctk.CTkFont(size=12), text_color="#8ea3c7").pack(anchor="w", padx=28)

        form = ctk.CTkScrollableFrame(dialog, fg_color="transparent", scrollbar_button_color="#1c2b48", scrollbar_button_hover_color="#27406b")
        form.pack(fill="both", expand=True, padx=24, pady=(16, 10))
        entries, textareas = {}, {}

        def add_entry(label, key, default="", placeholder=""):
            ctk.CTkLabel(form, text=label, font=ctk.CTkFont(size=12, weight="bold"), text_color="#9bb0d5").pack(anchor="w", pady=(8, 4))
            entry = ctk.CTkEntry(form, height=40, corner_radius=10, fg_color="#101b35", border_color="#233154", placeholder_text=placeholder)
            entry.insert(0, str(project.get(key, "") or default) if project else str(default or ""))
            entry.pack(fill="x")
            entries[key] = entry

        def add_menu(label, key, values, default):
            ctk.CTkLabel(form, text=label, font=ctk.CTkFont(size=12, weight="bold"), text_color="#9bb0d5").pack(anchor="w", pady=(8, 4))
            current_value = project.get(key) if project and project.get(key) is not None else default
            current = str(current_value)
            options = list(values)
            if current and current not in options:
                options = [current] + options
            var = ctk.StringVar(value=current)
            ctk.CTkOptionMenu(form, values=options, variable=var, fg_color="#152140", button_color="#233154", button_hover_color="#31446b", dropdown_fg_color="#111d39", corner_radius=10, height=40).pack(fill="x")
            entries[key] = var

        def add_textarea(label, key, height):
            ctk.CTkLabel(form, text=label, font=ctk.CTkFont(size=12, weight="bold"), text_color="#9bb0d5").pack(anchor="w", pady=(10, 4))
            box = ctk.CTkTextbox(form, height=height, corner_radius=12, fg_color="#101b35", border_color="#233154", border_width=1, wrap="word")
            box.insert("1.0", str(project.get(key, "") or "") if project else "")
            box.pack(fill="x")
            textareas[key] = box

        def set_entry_value(key, value):
            entry = entries[key]
            if hasattr(entry, "delete"):
                entry.delete(0, "end")
                if value:
                    entry.insert(0, value)

        add_entry("Project Name *", "name", placeholder="Pinaki North Ridge Heights")
        add_entry("Location", "location", placeholder="Uttara, Dhaka")
        add_menu("Property Type", "property_type", ["Apartment/Flats", "Independent House", "Duplex Home", "Studio Apartment", "Penthouse", "Residential Plot", "Commercial Office", "Shop/Retail", "Commercial Plot", "Agricultural Land", "Industrial Space"], "Apartment/Flats")
        add_menu("Property For", "property_for", LISTING_OPTIONS, "Sale")
        add_menu("Construction Status", "construction_status", CONSTRUCTION_OPTIONS, "Under Construction")
        add_entry("Property Size", "unit_size", placeholder="1100 sqft")
        add_menu("Transaction Type", "transaction_type", TRANSACTION_OPTIONS, "New")
        add_menu("Floor Available On", "floor_available_on", ["Any Floor", "Ground Floor", "1st-5th Floor", "6th-10th Floor", "11th-15th Floor", "16th+ Floor", "Top Floor", "Basement"], "Any Floor")
        add_menu("Bedrooms", "bedrooms", BEDROOM_OPTIONS, "3")
        add_menu("Bathrooms", "bathrooms", BATHROOM_OPTIONS, "3")
        add_menu("Balconies", "balconies", BALCONY_OPTIONS, "2")
        add_menu("Garages", "garages", GARAGE_OPTIONS, "No Parking")
        add_menu("Furnishing", "furnishing", ["Unfurnished", "Semi-furnished", "Fully Furnished"], "Unfurnished")
        add_menu("Facing", "facing", ["North Facing", "South Facing", "East Facing", "West Facing", "North-East Facing", "South-East Facing", "North-West Facing", "South-West Facing"], "North Facing")
        add_entry("Land Area", "land_area", placeholder="25 katha")
        add_entry("Building Area", "building_area", placeholder="120000 sqft")
        add_menu("Total Floors", "total_floors", FLOOR_RANGE_OPTIONS, "0")
        add_menu("Total Units", "total_units", TOTAL_UNIT_OPTIONS, "12")
        add_entry("Total Budget", "total_budget", default="0")
        add_entry("Progress (%)", "progress", default="0")
        add_entry("Start Date", "start_date", placeholder="YYYY-MM-DD")
        add_entry("Expected Completion", "estimated_end_date", placeholder="YYYY-MM-DD")

        ctk.CTkLabel(form, text="Project Cover Image", font=ctk.CTkFont(size=12, weight="bold"), text_color="#9bb0d5").pack(anchor="w", pady=(8, 4))
        image_row = ctk.CTkFrame(form, fg_color="transparent")
        image_row.pack(fill="x")
        cover_entry = ctk.CTkEntry(image_row, height=40, corner_radius=10, fg_color="#101b35", border_color="#233154", placeholder_text="Upload or paste a local image path")
        cover_entry.insert(0, str(project.get("cover_image_path", "") or "") if project else "")
        cover_entry.pack(side="left", fill="x", expand=True)
        entries["cover_image_path"] = cover_entry

        def refresh_preview():
            preview_path = resolve_image_path(cover_entry.get().strip(), APP_DIR)
            if preview_path:
                image_hint.configure(text=f"Selected image: {os.path.basename(preview_path)}", text_color="#d8e4ff")
            else:
                image_hint.configure(text="Upload a JPG, PNG, WEBP, or GIF to show a project hero image.", text_color="#8ea3c7")

        def choose_image():
            source_path = filedialog.askopenfilename(
                title="Select Project Image",
                filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.webp;*.gif"), ("All files", "*.*")],
            )
            if not source_path:
                return
            try:
                stored_path = store_project_image(source_path, APP_DIR)
            except Exception as exc:
                messagebox.showerror("Image Upload", str(exc))
                return
            set_entry_value("cover_image_path", stored_path)
            refresh_preview()

        ctk.CTkButton(image_row, text="Upload", width=92, height=40, corner_radius=10, fg_color="#4f8cff", hover_color="#3578f6", command=choose_image).pack(side="left", padx=(10, 0))
        ctk.CTkButton(image_row, text="Clear", width=74, height=40, corner_radius=10, fg_color="#182748", hover_color="#223660", command=lambda: [set_entry_value("cover_image_path", ""), refresh_preview()]).pack(side="left", padx=(8, 0))

        image_hint = ctk.CTkLabel(form, text="", font=ctk.CTkFont(size=11), text_color="#8ea3c7")
        image_hint.pack(anchor="w", pady=(6, 0))
        refresh_preview()

        add_menu("Project Type", "type", TYPE_OPTIONS, "residential")
        add_menu("Workflow Status", "status", ["planning", "active", "paused", "completed", "cancelled"], "planning")
        add_textarea("Property Description", "description", 180)
        add_textarea("Property Features", "features", 140)
        add_textarea("Nearby Institutions / Highlights", "nearby_places", 140)
        add_textarea("Corporate Office / Sales Note", "corporate_office", 110)

        def get_value(key):
            item = entries[key]
            return item.get().strip() if hasattr(item, "get") else str(item).strip()

        def save():
            name = get_value("name")
            if not name:
                messagebox.showwarning("Validation", "Project name is required.")
                return
            try:
                payload = {
                    "name": name,
                    "location": get_value("location") or None,
                    "property_type": get_value("property_type") or None,
                    "property_for": get_value("property_for").title() or None,
                    "construction_status": get_value("construction_status") or None,
                    "unit_size": get_value("unit_size") or None,
                    "transaction_type": get_value("transaction_type") or None,
                    "floor_available_on": get_value("floor_available_on") or None,
                    "bedrooms": get_value("bedrooms") or None,
                    "bathrooms": get_value("bathrooms") or None,
                    "balconies": get_value("balconies") or None,
                    "garages": get_value("garages") or None,
                    "furnishing": get_value("furnishing") or None,
                    "facing": get_value("facing") or None,
                    "land_area": get_value("land_area") or None,
                    "building_area": get_value("building_area") or None,
                    "total_floors": safe_int(get_value("total_floors")),
                    "total_units": safe_int(get_value("total_units")),
                    "total_budget": safe_float(get_value("total_budget")),
                    "progress": safe_float(get_value("progress")),
                    "start_date": validate_date(get_value("start_date"), "Start date"),
                    "estimated_end_date": validate_date(get_value("estimated_end_date"), "Expected completion"),
                    "cover_image_path": get_value("cover_image_path") or None,
                    "type": get_value("type") or "residential",
                    "status": get_value("status") or "planning",
                    "description": textareas["description"].get("1.0", "end").strip() or None,
                    "features": textareas["features"].get("1.0", "end").strip() or None,
                    "nearby_places": textareas["nearby_places"].get("1.0", "end").strip() or None,
                    "corporate_office": textareas["corporate_office"].get("1.0", "end").strip() or None,
                }
                cols = list(payload.keys())
                vals = tuple(payload[col] for col in cols)
                if project:
                    assignments = ", ".join(f"{col}=%s" for col in cols)
                    execute_query(f"UPDATE projects SET {assignments}, updated_at=NOW() WHERE id=%s", vals + (project["id"],), fetch=False)
                else:
                    insert_cols = cols + ["created_by"]
                    execute_query(
                        f"INSERT INTO projects ({', '.join(insert_cols)}, created_at, updated_at) VALUES ({', '.join(['%s'] * len(insert_cols))}, NOW(), NOW())",
                        vals + (self.user.get("id"),),
                        fetch=False,
                    )
            except ValueError as exc:
                messagebox.showwarning("Validation", str(exc))
                return
            except Exception as exc:
                messagebox.showerror("Error", str(exc))
                return
            dialog.destroy()
            self.load_data()

        footer = ctk.CTkFrame(dialog, fg_color="transparent")
        footer.pack(fill="x", padx=24, pady=(0, 18))
        ctk.CTkButton(footer, text="Cancel", fg_color="#182748", hover_color="#223660", corner_radius=10, height=38, command=dialog.destroy).pack(side="left")
        ctk.CTkButton(footer, text="Save Project", fg_color="#4f8cff", hover_color="#3578f6", corner_radius=10, height=38, command=save).pack(side="right")

    def delete_project(self, project_id):
        if not messagebox.askyesno(
            "Confirm Delete",
            "Delete this project and related records?\n\nThe project and linked data will be moved to Recycle Bin.",
        ):
            return
        try:
            delete_project_service(int(project_id), deleted_by=self.user.get("id"))
            self.load_data()
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
