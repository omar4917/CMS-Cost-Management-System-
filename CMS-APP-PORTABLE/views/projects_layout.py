"""
Layout helpers for Projects view.
Extracts reusable UI pieces from the view controller.
"""

from __future__ import annotations

import customtkinter as ctk

from views.projects_shared import display, format_currency, humanize, safe_float, STATUS_COLORS


class MetricCard(ctk.CTkFrame):
    def __init__(self, parent, label, color):
        super().__init__(
            parent,
            fg_color="#111d39",
            corner_radius=16,
            border_width=1,
            border_color="#233154",
            height=88,
        )
        self.pack_propagate(False)
        ctk.CTkLabel(self, text=label, font=ctk.CTkFont(size=11), text_color="#7184aa").pack(
            anchor="w", padx=16, pady=(14, 0)
        )
        self.value_label = ctk.CTkLabel(self, text="-", font=ctk.CTkFont(size=22, weight="bold"), text_color=color)
        self.value_label.pack(anchor="w", padx=16, pady=(5, 0))

    def set_value(self, text):
        self.value_label.configure(text=text)


class ProjectCard(ctk.CTkFrame):
    def __init__(self, parent, project, index, on_open, on_edit, on_delete):
        super().__init__(
            parent,
            fg_color="#0d1630",
            corner_radius=22,
            border_width=1,
            border_color="#223356",
        )
        self.grid(row=index // 2, column=index % 2, sticky="nsew", padx=6, pady=6)

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=18, pady=(16, 8))
        badges = ctk.CTkFrame(content, fg_color="transparent")
        badges.pack(fill="x")
        ctk.CTkLabel(
            badges,
            text=display(project.get("property_for"), "Listing").upper(),
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#08111f",
            fg_color="#f6c85f",
            corner_radius=8,
            padx=10,
            pady=4,
        ).pack(side="left")
        status = str(project.get("status") or "planning").lower()
        ctk.CTkLabel(
            badges,
            text=humanize(status),
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#f8fafc",
            fg_color=STATUS_COLORS.get(status, "#4b5563"),
            corner_radius=8,
            padx=10,
            pady=4,
        ).pack(side="right")

        ctk.CTkLabel(
            content,
            text=display(project.get("name")),
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#f8fafc",
            wraplength=500,
            justify="left",
        ).pack(anchor="w", pady=(14, 4))
        ctk.CTkLabel(
            content,
            text=display(project.get("location"), "Location pending"),
            font=ctk.CTkFont(size=12),
            text_color="#8ea3c7",
        ).pack(anchor="w")

        specs = ctk.CTkFrame(content, fg_color="transparent")
        specs.pack(fill="x", pady=(14, 10))
        for label, value in [
            ("Type", project.get("property_type") or humanize(project.get("type")) or "Residential"),
            ("Size", project.get("unit_size") or project.get("building_area") or "TBD"),
            ("Bed", project.get("bedrooms") or "TBD"),
            ("Floors", project.get("total_floors") or "TBD"),
        ]:
            pill = ctk.CTkFrame(
                specs,
                fg_color="#111d39",
                corner_radius=14,
                border_width=1,
                border_color="#233154",
                height=64,
            )
            pill.pack(side="left", fill="x", expand=True, padx=(0, 8))
            pill.pack_propagate(False)
            ctk.CTkLabel(
                pill,
                text=label,
                font=ctk.CTkFont(size=11),
                text_color="#7184aa",
            ).pack(fill="x", padx=14, pady=(11, 0))
            ctk.CTkLabel(
                pill,
                text=display(value, "TBD"),
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#f8fafc",
            ).pack(fill="x", padx=14, pady=(4, 0))

        desc = str(project.get("description") or "").strip()
        snippet = desc[:170] + ("..." if len(desc) > 170 else "")
        ctk.CTkLabel(
            content,
            text=snippet or "Add a detailed description to make the project feel like a full property profile.",
            font=ctk.CTkFont(size=12),
            text_color="#c7d5f2",
            wraplength=540,
            justify="left",
        ).pack(anchor="w", pady=(4, 12))

        progress = max(0, min(safe_float(project.get("progress")), 100))
        row = ctk.CTkFrame(content, fg_color="transparent")
        row.pack(fill="x")
        ctk.CTkLabel(row, text="Construction Progress", font=ctk.CTkFont(size=11), text_color="#7184aa").pack(
            side="left"
        )
        ctk.CTkLabel(
            row,
            text=f"{progress:.0f}%",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#9bb0d5",
        ).pack(side="right")
        bar = ctk.CTkProgressBar(content, height=8, corner_radius=6, fg_color="#13223f", progress_color="#4f8cff")
        bar.set(progress / 100)
        bar.pack(fill="x", pady=(6, 0))
        if on_open:
            self._bind_click(content, lambda _event: on_open(project))

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", padx=18, pady=(0, 16))
        ctk.CTkButton(
            footer,
            text="Open Showcase",
            height=34,
            corner_radius=10,
            fg_color="#4f8cff",
            hover_color="#3578f6",
            command=lambda: on_open(project) if on_open else None,
        ).pack(side="left")
        ctk.CTkButton(
            footer,
            text="Edit",
            width=70,
            height=34,
            corner_radius=10,
            fg_color="#182748",
            hover_color="#223660",
            command=lambda: on_edit(project) if on_edit else None,
        ).pack(side="right")
        ctk.CTkButton(
            footer,
            text="Delete",
            width=78,
            height=34,
            corner_radius=10,
            fg_color="#182748",
            hover_color="#7f1d1d",
            text_color="#ff9aa2",
            command=lambda: on_delete(project.get("id")) if on_delete else None,
        ).pack(side="right", padx=(0, 8))

    def _bind_click(self, widget, callback):
        if isinstance(widget, ctk.CTkButton):
            return
        widget.bind("<Button-1>", callback)
        for child in widget.winfo_children():
            self._bind_click(child, callback)


class ProjectsLayout:
    def __init__(self, parent, on_new, on_auto_covers, on_bulk_delete, on_filters_change):
        self.scroll = ctk.CTkScrollableFrame(
            parent,
            fg_color="transparent",
            scrollbar_button_color="#1c2b48",
            scrollbar_button_hover_color="#27406b",
        )
        self.scroll.pack(fill="both", expand=True)

        hero = ctk.CTkFrame(self.scroll, fg_color="#0d1630", corner_radius=24, border_width=1, border_color="#233154")
        hero.pack(fill="x", pady=(0, 14))

        header = ctk.CTkFrame(hero, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 12))
        col = ctk.CTkFrame(header, fg_color="transparent")
        col.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(col, text="Project Showcase", font=ctk.CTkFont(size=28, weight="bold"), text_color="#f8fafc").pack(
            anchor="w"
        )
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
            command=on_new,
        ).pack(side="right")
        ctk.CTkButton(
            header,
            text="Auto Covers",
            fg_color="#182748",
            hover_color="#223660",
            corner_radius=12,
            height=42,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=on_auto_covers,
        ).pack(side="right", padx=(0, 10))
        ctk.CTkButton(
            header,
            text="Bulk Delete",
            fg_color="#ef4444",
            hover_color="#dc2626",
            corner_radius=12,
            height=42,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=on_bulk_delete,
        ).pack(side="right", padx=(0, 10))

        filters = ctk.CTkFrame(hero, fg_color="transparent")
        filters.pack(fill="x", padx=24, pady=(0, 18))
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_args: on_filters_change())
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
            command=lambda _value: on_filters_change(),
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
            command=lambda _value: on_filters_change(),
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

        self.metric_cards = {
            "projects": MetricCard(metrics, "Projects", "#4f8cff"),
            "active": MetricCard(metrics, "Active", "#27d3a2"),
            "budget": MetricCard(metrics, "Portfolio Budget", "#f6c85f"),
            "progress": MetricCard(metrics, "Avg Progress", "#9bb0d5"),
        }
        for idx, key in enumerate(["projects", "active", "budget", "progress"]):
            self.metric_cards[key].grid(row=0, column=idx, sticky="nsew", padx=5, pady=4)

        self.cards_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.cards_frame.pack(fill="both", expand=True)
        self.cards_frame.grid_columnconfigure(0, weight=1)
        self.cards_frame.grid_columnconfigure(1, weight=1)

    def clear_cards(self):
        for widget in self.cards_frame.winfo_children():
            widget.destroy()

    def show_error(self, message):
        ctk.CTkLabel(self.cards_frame, text=message, text_color="#ef4444").grid(
            row=0, column=0, padx=8, pady=20, sticky="w"
        )

    def show_empty(self):
        empty = ctk.CTkFrame(self.cards_frame, fg_color="#0d1630", corner_radius=20, border_width=1, border_color="#1f2a45")
        empty.grid(row=0, column=0, columnspan=2, sticky="ew", padx=6, pady=8)
        ctk.CTkLabel(
            empty,
            text="No projects found",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#d8e4ff",
        ).pack(anchor="w", padx=22, pady=(22, 6))
        ctk.CTkLabel(
            empty,
            text="Create a project and fill its listing details to unlock the desktop showcase view.",
            font=ctk.CTkFont(size=12),
            text_color="#6e84ac",
        ).pack(anchor="w", padx=22, pady=(0, 22))

    def set_metrics(self, metrics):
        self.metric_cards["projects"].set_value(str(metrics["total"]))
        self.metric_cards["active"].set_value(str(metrics["active"]))
        self.metric_cards["budget"].set_value(format_currency(metrics["budget"]))
        self.metric_cards["progress"].set_value(f"{metrics['avg_progress']:.0f}%")

    def render_projects(self, projects, on_open, on_edit, on_delete):
        for idx, project in enumerate(projects):
            ProjectCard(self.cards_frame, project, idx, on_open, on_edit, on_delete)
