"""
Projects view for the desktop app.
Adds richer project listing fields and a property-style showcase dialog.
"""

import os
import sys
from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk

try:
    from PIL import Image
except ImportError:
    Image = None

from core.database import ensure_project_profile_columns, execute_query


if getattr(sys, "frozen", False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


STATUS_COLORS = {
    "planning": "#4f8cff",
    "active": "#27d3a2",
    "paused": "#f6c85f",
    "completed": "#9b8cff",
    "cancelled": "#ff7a90",
}

TYPE_OPTIONS = ["residential", "commercial", "mixed", "industrial", "land_development", "renovation"]

DETAIL_FIELDS = [
    ("Property Type", "property_type"),
    ("Property For", "property_for"),
    ("Location", "location"),
    ("Construction Status", "construction_status"),
    ("Property Size", "unit_size"),
    ("Transaction Type", "transaction_type"),
    ("Floor Available On", "floor_available_on"),
    ("Bedroom", "bedrooms"),
    ("Baths", "bathrooms"),
    ("Balconies", "balconies"),
    ("Garages", "garages"),
    ("Total Floor", "total_floors"),
    ("Furnishing", "furnishing"),
    ("Facing", "facing"),
    ("Land Area", "land_area"),
    ("Building Area", "building_area"),
    ("Start Date", "start_date"),
    ("Expected Completion", "estimated_end_date"),
]


def _safe_float(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _safe_int(value):
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0


def _humanize(value):
    text = str(value or "").replace("_", " ").strip()
    return text.title() if text else ""


def _display(value, fallback="Not added yet"):
    text = str(value or "").strip()
    return text if text else fallback


def _format_currency(value):
    return f"BDT {_safe_float(value):,.0f}"


def _format_date(value):
    if not value:
        return "TBD"
    if isinstance(value, datetime):
        return value.strftime("%d %b %Y")
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).strftime("%d %b %Y")
        except ValueError:
            continue
    return text or "TBD"


def _split_items(value):
    items = []
    for line in str(value or "").replace("\r", "\n").split("\n"):
        for part in line.split(","):
            cleaned = part.strip().lstrip("-").lstrip("*").strip()
            if cleaned:
                items.append(cleaned)
    return items


def _validate_date(value, label):
    text = str(value or "").strip()
    if not text:
        return None
    try:
        datetime.strptime(text, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"{label} must use YYYY-MM-DD.") from exc
    return text


def _resolve_image_path(value):
    path = str(value or "").strip()
    if not path:
        return None
    if os.path.isabs(path) and os.path.exists(path):
        return path
    local = os.path.join(APP_DIR, path)
    if os.path.exists(local):
        return local
    return path if os.path.exists(path) else None


class ProjectsView(ctk.CTkFrame):
    def __init__(self, parent, user):
        super().__init__(parent, fg_color="transparent")
        ensure_project_profile_columns()
        self.user = user
        self.projects = []
        self.metric_labels = {}

        self.scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color="#1c2b48",
            scrollbar_button_hover_color="#27406b",
        )
        self.scroll.pack(fill="both", expand=True)

        self.build_ui()
        self.load_data()

    def build_ui(self):
        hero = ctk.CTkFrame(self.scroll, fg_color="#0d1630", corner_radius=24, border_width=1, border_color="#233154")
        hero.pack(fill="x", pady=(0, 14))

        header = ctk.CTkFrame(hero, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 12))
        col = ctk.CTkFrame(header, fg_color="transparent")
        col.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(col, text="Project Showcase", font=ctk.CTkFont(size=28, weight="bold"), text_color="#f8fafc").pack(anchor="w")
        ctk.CTkLabel(
            col,
            text="Open a project like a premium property profile with specs, features, and long-form description.",
            font=ctk.CTkFont(size=13),
            text_color="#8ea3c7",
        ).pack(anchor="w", pady=(4, 0))
        ctk.CTkButton(
            header,
            text="+ New Project",
            fg_color="#4f8cff",
            hover_color="#3578f6",
            corner_radius=12,
            height=42,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.open_add_dialog,
        ).pack(side="right")

        filters = ctk.CTkFrame(hero, fg_color="transparent")
        filters.pack(fill="x", padx=24, pady=(0, 18))
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_args: self.load_data())
        ctk.CTkEntry(
            filters,
            textvariable=self.search_var,
            placeholder_text="Search name, location, property type, listing purpose, or description...",
            height=42,
            width=390,
            corner_radius=12,
            fg_color="#101b35",
            border_color="#233154",
        ).pack(side="left")

        self.status_var = ctk.StringVar(value="All Statuses")
        ctk.CTkOptionMenu(
            filters,
            variable=self.status_var,
            values=["All Statuses", "planning", "active", "paused", "completed", "cancelled"],
            command=lambda _value: self.load_data(),
            fg_color="#152140",
            button_color="#233154",
            button_hover_color="#31446b",
            dropdown_fg_color="#111d39",
            corner_radius=10,
            height=42,
            width=170,
        ).pack(side="left", padx=(10, 0))

        self.purpose_var = ctk.StringVar(value="All Listings")
        ctk.CTkOptionMenu(
            filters,
            variable=self.purpose_var,
            values=["All Listings", "Sale", "Rent", "Lease", "Joint Venture", "Other"],
            command=lambda _value: self.load_data(),
            fg_color="#152140",
            button_color="#233154",
            button_hover_color="#31446b",
            dropdown_fg_color="#111d39",
            corner_radius=10,
            height=42,
            width=170,
        ).pack(side="left", padx=(10, 0))

        metrics = ctk.CTkFrame(self.scroll, fg_color="transparent")
        metrics.pack(fill="x", pady=(0, 12))
        for idx in range(4):
            metrics.grid_columnconfigure(idx, weight=1)
        for col_idx, key, label, color in [
            (0, "projects", "Projects", "#4f8cff"),
            (1, "active", "Active", "#27d3a2"),
            (2, "budget", "Portfolio Budget", "#f6c85f"),
            (3, "progress", "Avg Progress", "#9bb0d5"),
        ]:
            card = ctk.CTkFrame(metrics, fg_color="#111d39", corner_radius=16, border_width=1, border_color="#233154", height=88)
            card.grid(row=0, column=col_idx, sticky="nsew", padx=5, pady=4)
            card.pack_propagate(False)
            ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=11), text_color="#7184aa").pack(anchor="w", padx=16, pady=(14, 0))
            val = ctk.CTkLabel(card, text="-", font=ctk.CTkFont(size=22, weight="bold"), text_color=color)
            val.pack(anchor="w", padx=16, pady=(5, 0))
            self.metric_labels[key] = val

        self.cards_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.cards_frame.pack(fill="both", expand=True)
        self.cards_frame.grid_columnconfigure(0, weight=1)
        self.cards_frame.grid_columnconfigure(1, weight=1)

    def load_data(self):
        for widget in self.cards_frame.winfo_children():
            widget.destroy()

        query = "SELECT * FROM projects WHERE 1=1"
        params = []
        search = self.search_var.get().strip()
        if search:
            query += (
                " AND (name LIKE %s OR location LIKE %s OR description LIKE %s "
                "OR property_type LIKE %s OR property_for LIKE %s OR construction_status LIKE %s)"
            )
            like = f"%{search}%"
            params.extend([like, like, like, like, like, like])
        if self.status_var.get() != "All Statuses":
            query += " AND status=%s"
            params.append(self.status_var.get())
        if self.purpose_var.get() != "All Listings":
            query += " AND LOWER(COALESCE(property_for, ''))=%s"
            params.append(self.purpose_var.get().lower())
        query += " ORDER BY created_at DESC, id DESC"

        try:
            self.projects = execute_query(query, params)
        except Exception as exc:
            ctk.CTkLabel(self.cards_frame, text=f"Error loading projects: {exc}", text_color="#ef4444").grid(row=0, column=0, padx=8, pady=20, sticky="w")
            return

        total = len(self.projects)
        self.metric_labels["projects"].configure(text=str(total))
        self.metric_labels["active"].configure(text=str(sum(1 for p in self.projects if str(p.get("status", "")).lower() == "active")))
        self.metric_labels["budget"].configure(text=_format_currency(sum(_safe_float(p.get("total_budget")) for p in self.projects)))
        avg = sum(_safe_float(p.get("progress")) for p in self.projects) / total if total else 0
        self.metric_labels["progress"].configure(text=f"{avg:.0f}%")

        if not self.projects:
            empty = ctk.CTkFrame(self.cards_frame, fg_color="#0d1630", corner_radius=20, border_width=1, border_color="#1f2a45")
            empty.grid(row=0, column=0, columnspan=2, sticky="ew", padx=6, pady=8)
            ctk.CTkLabel(empty, text="No projects found", font=ctk.CTkFont(size=22, weight="bold"), text_color="#d8e4ff").pack(anchor="w", padx=22, pady=(22, 6))
            ctk.CTkLabel(empty, text="Create a project and fill its listing details to unlock the desktop showcase view.", font=ctk.CTkFont(size=12), text_color="#6e84ac").pack(anchor="w", padx=22, pady=(0, 22))
            return

        for idx, project in enumerate(self.projects):
            self._create_project_card(idx, project)

    def _create_project_card(self, idx, project):
        card = ctk.CTkFrame(self.cards_frame, fg_color="#0d1630", corner_radius=22, border_width=1, border_color="#223356")
        card.grid(row=idx // 2, column=idx % 2, sticky="nsew", padx=6, pady=6)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=18, pady=(16, 8))
        badges = ctk.CTkFrame(content, fg_color="transparent")
        badges.pack(fill="x")
        ctk.CTkLabel(badges, text=_display(project.get("property_for"), "Listing").upper(), font=ctk.CTkFont(size=10, weight="bold"), text_color="#08111f", fg_color="#f6c85f", corner_radius=8, padx=10, pady=4).pack(side="left")
        status = str(project.get("status") or "planning").lower()
        ctk.CTkLabel(badges, text=_humanize(status), font=ctk.CTkFont(size=10, weight="bold"), text_color="#f8fafc", fg_color=STATUS_COLORS.get(status, "#4b5563"), corner_radius=8, padx=10, pady=4).pack(side="right")

        ctk.CTkLabel(content, text=_display(project.get("name")), font=ctk.CTkFont(size=22, weight="bold"), text_color="#f8fafc", wraplength=500, justify="left").pack(anchor="w", pady=(14, 4))
        ctk.CTkLabel(content, text=_display(project.get("location"), "Location pending"), font=ctk.CTkFont(size=12), text_color="#8ea3c7").pack(anchor="w")

        specs = ctk.CTkFrame(content, fg_color="transparent")
        specs.pack(fill="x", pady=(14, 10))
        for label, value in [
            ("Type", project.get("property_type") or _humanize(project.get("type")) or "Residential"),
            ("Size", project.get("unit_size") or project.get("building_area") or "TBD"),
            ("Bed", project.get("bedrooms") or "TBD"),
            ("Floors", project.get("total_floors") or "TBD"),
        ]:
            pill = ctk.CTkFrame(specs, fg_color="#111d39", corner_radius=14, border_width=1, border_color="#233154", height=64)
            pill.pack(side="left", fill="x", expand=True, padx=(0, 8))
            pill.pack_propagate(False)
            ctk.CTkLabel(pill, text=label, font=ctk.CTkFont(size=11), text_color="#7184aa").pack(anchor="w", padx=14, pady=(11, 0))
            ctk.CTkLabel(pill, text=_display(value, "TBD"), font=ctk.CTkFont(size=13, weight="bold"), text_color="#f8fafc").pack(anchor="w", padx=14, pady=(4, 0))

        desc = str(project.get("description") or "").strip()
        snippet = desc[:170] + ("..." if len(desc) > 170 else "")
        ctk.CTkLabel(content, text=snippet or "Add a detailed description to make the project feel like a full property profile.", font=ctk.CTkFont(size=12), text_color="#c7d5f2", wraplength=540, justify="left").pack(anchor="w", pady=(4, 12))

        progress = max(0, min(_safe_float(project.get("progress")), 100))
        row = ctk.CTkFrame(content, fg_color="transparent")
        row.pack(fill="x")
        ctk.CTkLabel(row, text="Construction Progress", font=ctk.CTkFont(size=11), text_color="#7184aa").pack(side="left")
        ctk.CTkLabel(row, text=f"{progress:.0f}%", font=ctk.CTkFont(size=11, weight="bold"), text_color="#9bb0d5").pack(side="right")
        bar = ctk.CTkProgressBar(content, height=8, corner_radius=6, fg_color="#13223f", progress_color="#4f8cff")
        bar.set(progress / 100)
        bar.pack(fill="x", pady=(6, 0))
        self._bind_click(content, lambda _event, item=project: self.open_project_detail(item))

        footer = ctk.CTkFrame(card, fg_color="transparent")
        footer.pack(fill="x", padx=18, pady=(0, 16))
        ctk.CTkButton(footer, text="Open Showcase", height=34, corner_radius=10, fg_color="#4f8cff", hover_color="#3578f6", command=lambda item=project: self.open_project_detail(item)).pack(side="left")
        ctk.CTkButton(footer, text="Edit", width=70, height=34, corner_radius=10, fg_color="#182748", hover_color="#223660", command=lambda item=project: self.open_edit_dialog(item)).pack(side="right")
        ctk.CTkButton(footer, text="Delete", width=78, height=34, corner_radius=10, fg_color="#182748", hover_color="#7f1d1d", text_color="#ff9aa2", command=lambda pid=project["id"]: self.delete_project(pid)).pack(side="right", padx=(0, 8))

    def _bind_click(self, widget, callback):
        widget.bind("<Button-1>", callback)
        for child in widget.winfo_children():
            self._bind_click(child, callback)

    def open_add_dialog(self):
        self._open_dialog(None)

    def open_edit_dialog(self, project):
        self._open_dialog(project)

    def open_project_detail(self, project):
        rows = execute_query("SELECT * FROM projects WHERE id=%s", (project["id"],))
        if not rows:
            messagebox.showwarning("Missing Project", "This project could not be loaded.")
            self.load_data()
            return
        project = rows[0]

        try:
            investments = execute_query("SELECT COALESCE(SUM(amount),0) AS total FROM investments WHERE project_id=%s AND status='confirmed'", (project["id"],))[0]["total"]
            collections = execute_query("SELECT COALESCE(SUM(CASE WHEN paid_amount > 0 THEN paid_amount ELSE amount END),0) AS total FROM payment_schedules WHERE project_id=%s AND status='paid'", (project["id"],))[0]["total"]
            costs = execute_query("SELECT COALESCE(SUM(actual_amount),0) AS total FROM cost_items WHERE project_id=%s AND status NOT IN ('cancelled','rejected')", (project["id"],))[0]["total"]
            contractors = execute_query("SELECT COALESCE(SUM(amount),0) AS total FROM contractor_payments WHERE project_id=%s AND status IN ('paid','approved','completed')", (project["id"],))[0]["total"]
        except Exception:
            investments = collections = costs = contractors = 0
        net = _safe_float(investments) + _safe_float(collections) - _safe_float(costs) - _safe_float(contractors)

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
        ctk.CTkLabel(title, text=_display(project.get("name")), font=ctk.CTkFont(size=30, weight="bold"), text_color="#f8fafc").pack(anchor="w")
        ctk.CTkLabel(title, text=_display(project.get("location"), "Location pending"), font=ctk.CTkFont(size=13), text_color="#8ea3c7").pack(anchor="w", pady=(4, 0))
        badge_col = ctk.CTkFrame(top, fg_color="transparent")
        badge_col.pack(side="right")
        ctk.CTkLabel(badge_col, text=_display(project.get("property_for"), "Listing").upper(), font=ctk.CTkFont(size=11, weight="bold"), text_color="#08111f", fg_color="#f6c85f", corner_radius=10, padx=12, pady=6).pack(anchor="e")
        ctk.CTkLabel(badge_col, text=_humanize(project.get("status") or "planning"), font=ctk.CTkFont(size=11, weight="bold"), text_color="#f8fafc", fg_color=STATUS_COLORS.get(str(project.get("status") or "planning").lower(), "#4b5563"), corner_radius=10, padx=12, pady=6).pack(anchor="e", pady=(8, 0))

        body = ctk.CTkFrame(hero, fg_color="transparent")
        body.pack(fill="x", padx=24, pady=(0, 24))
        body.grid_columnconfigure(0, weight=11)
        body.grid_columnconfigure(1, weight=9)
        visual = ctk.CTkFrame(body, fg_color="#0d1630", corner_radius=24, border_width=1, border_color="#223356", height=380)
        visual.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        visual.pack_propagate(False)

        image_path = _resolve_image_path(project.get("cover_image_path"))
        if image_path and Image is not None:
            try:
                cover = ctk.CTkImage(Image.open(image_path), size=(700, 380))
                dialog._project_cover = cover
                ctk.CTkLabel(visual, text="", image=cover).pack(fill="both", expand=True, padx=10, pady=10)
            except Exception:
                image_path = None
        if not image_path:
            inner = ctk.CTkFrame(visual, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=24, pady=24)
            initials = "".join(part[:1] for part in str(project.get("name") or "P").split()[:2]).upper() or "P"
            ctk.CTkLabel(inner, text=_display(project.get("property_type") or _humanize(project.get("type")), "Residential Tower").upper(), font=ctk.CTkFont(size=11, weight="bold"), text_color="#8ea3c7").pack(anchor="w")
            badge = ctk.CTkFrame(inner, fg_color="#4f8cff", width=96, height=96, corner_radius=28)
            badge.pack(anchor="w", pady=(18, 16))
            badge.pack_propagate(False)
            ctk.CTkLabel(badge, text=initials, font=ctk.CTkFont(size=34, weight="bold"), text_color="#f8fafc").pack(expand=True)
            ctk.CTkLabel(inner, text=_display(project.get("name")), font=ctk.CTkFont(size=30, weight="bold"), text_color="#f8fafc", wraplength=560, justify="left").pack(anchor="w")
            ctk.CTkLabel(inner, text=_display(project.get("description"), "Add a cover image path to show a hero photo, or keep this rich placeholder layout for the desktop showcase."), font=ctk.CTkFont(size=13), text_color="#c7d5f2", wraplength=560, justify="left").pack(anchor="w", pady=(12, 0))

        glance = ctk.CTkFrame(body, fg_color="#101b35", corner_radius=24, border_width=1, border_color="#233154")
        glance.grid(row=0, column=1, sticky="nsew")
        ctk.CTkLabel(glance, text="AT A GLANCE", font=ctk.CTkFont(size=22, weight="bold"), text_color="#f8fafc").pack(anchor="w", padx=22, pady=(18, 12))
        ctk.CTkFrame(glance, fg_color="#223356", height=1).pack(fill="x", padx=22)
        for label, key in DETAIL_FIELDS:
            value = _format_date(project.get(key)) if key in {"start_date", "estimated_end_date"} else _display(project.get(key), "TBD")
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
            (0, "Location", _display(project.get("location"), "TBD"), "#9bb0d5"),
            (1, "Apartment Size", _display(project.get("unit_size") or project.get("building_area"), "TBD"), "#f8fafc"),
            (2, "Bedroom", _display(project.get("bedrooms"), "TBD"), "#f8fafc"),
            (3, "Expected Completion", _format_date(project.get("estimated_end_date")), "#f8fafc"),
            (4, "Status", _display(project.get("construction_status") or _humanize(project.get("status")), "TBD"), "#27d3a2"),
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
            ctk.CTkLabel(card, text=_format_currency(value), font=ctk.CTkFont(size=16, weight="bold"), text_color=color).pack(anchor="w", padx=14, pady=(6, 0))

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
        box.insert("1.0", _display(text))
        box.configure(state="disabled")

    def _features_card(self, parent, column, value, pad):
        card = ctk.CTkFrame(parent, fg_color="#0d1630", corner_radius=22, border_width=1, border_color="#1f2a45")
        card.grid(row=0, column=column, sticky="nsew", padx=pad, pady=4)
        ctk.CTkLabel(card, text="Property Features", font=ctk.CTkFont(size=22, weight="bold"), text_color="#f8fafc").pack(anchor="w", padx=22, pady=(18, 12))
        items = _split_items(value)
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
            current = str(project.get(key) or default) if project else str(default)
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

        add_entry("Project Name *", "name", placeholder="Pinaki North Ridge Heights")
        add_entry("Location", "location", placeholder="Uttara, Dhaka")
        add_entry("Property Type", "property_type", placeholder="Apartment/Flats")
        add_entry("Property For", "property_for", placeholder="Sale")
        add_entry("Construction Status", "construction_status", placeholder="Almost Ready")
        add_entry("Property Size", "unit_size", placeholder="1100 sqft")
        add_entry("Transaction Type", "transaction_type", placeholder="New")
        add_entry("Floor Available On", "floor_available_on", placeholder="Any Floor")
        add_entry("Bedrooms", "bedrooms", placeholder="03")
        add_entry("Bathrooms", "bathrooms", placeholder="03")
        add_entry("Balconies", "balconies", placeholder="2")
        add_entry("Garages", "garages", placeholder="No Parking")
        add_entry("Furnishing", "furnishing", placeholder="Unfurnished")
        add_entry("Facing", "facing", placeholder="North Facing")
        add_entry("Land Area", "land_area", placeholder="25 katha")
        add_entry("Building Area", "building_area", placeholder="120000 sqft")
        add_entry("Total Floors", "total_floors", default="0")
        add_entry("Total Units", "total_units", default="0")
        add_entry("Total Budget", "total_budget", default="0")
        add_entry("Progress (%)", "progress", default="0")
        add_entry("Start Date", "start_date", placeholder="YYYY-MM-DD")
        add_entry("Expected Completion", "estimated_end_date", placeholder="YYYY-MM-DD")
        add_entry("Cover Image Path", "cover_image_path", placeholder="Optional local image path")
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
                    "total_floors": _safe_int(get_value("total_floors")),
                    "total_units": _safe_int(get_value("total_units")),
                    "total_budget": _safe_float(get_value("total_budget")),
                    "progress": _safe_float(get_value("progress")),
                    "start_date": _validate_date(get_value("start_date"), "Start date"),
                    "estimated_end_date": _validate_date(get_value("estimated_end_date"), "Expected completion"),
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
        if not messagebox.askyesno("Confirm Delete", "Delete this project? This cannot be undone."):
            return
        try:
            execute_query("DELETE FROM projects WHERE id=%s", (project_id,), fetch=False)
            self.load_data()
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
