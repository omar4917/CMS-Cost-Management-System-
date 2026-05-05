"""
Dashboard View for CMS Desktop App.
Premium design with stat cards, project progress, and activity feed.
"""

import customtkinter as ctk
from core.database import execute_query
from core.desktop_utils import format_date


class DashboardView(ctk.CTkFrame):
    def __init__(self, parent, user):
        super().__init__(parent, fg_color="transparent")
        self.user = user

        # Single scrollable container
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent",
                                              scrollbar_button_color="#1e293b",
                                              scrollbar_button_hover_color="#334155")
        self.scroll.pack(fill="both", expand=True)

        self.build_ui()
        self.load_data()

    def build_ui(self):
        # ── Header ──
        header = ctk.CTkFrame(self.scroll, fg_color="transparent")
        header.pack(fill="x", pady=(5, 25))

        greeting = f"Welcome back, {self.user.get('firstName', 'Admin')} 👋"
        ctk.CTkLabel(header, text=greeting,
                     font=ctk.CTkFont(size=24, weight="bold"),
                     text_color="#f1f5f9").pack(side="left")
        ctk.CTkLabel(header, text="Here's your real estate overview",
                     font=ctk.CTkFont(size=14),
                     text_color="#475569").pack(side="left", padx=(15, 0), pady=(4, 0))

        # ── Stats Row 1 ──
        self.stat_cards = []
        row1 = ctk.CTkFrame(self.scroll, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 12))
        for i in range(3):
            row1.grid_columnconfigure(i, weight=1)

        self.stat_data_r1 = [
            {"label": "Total Projects", "icon": "🏗️", "color": "#3b82f6", "accent": "#1d4ed8"},
            {"label": "Total Invested", "icon": "💰", "color": "#10b981", "accent": "#047857"},
            {"label": "Total Budget",   "icon": "📊", "color": "#8b5cf6", "accent": "#6d28d9"},
        ]
        for col, s in enumerate(self.stat_data_r1):
            card = self._create_stat_card(row1, col, s)
            self.stat_cards.append(card)

        # ── Stats Row 2 ──
        row2 = ctk.CTkFrame(self.scroll, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 25))
        for i in range(3):
            row2.grid_columnconfigure(i, weight=1)

        self.stat_data_r2 = [
            {"label": "Active Investors", "icon": "👥", "color": "#f59e0b", "accent": "#b45309"},
            {"label": "Overdue Payments", "icon": "⚠️", "color": "#ef4444", "accent": "#b91c1c"},
            {"label": "Active Projects",  "icon": "✅", "color": "#06b6d4", "accent": "#0e7490"},
        ]
        for col, s in enumerate(self.stat_data_r2):
            card = self._create_stat_card(row2, col, s)
            self.stat_cards.append(card)

        # ── Bottom Section (2 columns) ──
        bottom = ctk.CTkFrame(self.scroll, fg_color="transparent")
        bottom.pack(fill="both", expand=True)
        bottom.grid_columnconfigure(0, weight=1)
        bottom.grid_columnconfigure(1, weight=1)

        # Project Progress Panel
        self.progress_panel = ctk.CTkFrame(bottom, fg_color="#111827", corner_radius=16, border_width=1, border_color="#1e293b")
        self.progress_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 10))

        pg_header = ctk.CTkFrame(self.progress_panel, fg_color="transparent")
        pg_header.pack(fill="x", padx=20, pady=(18, 12))
        ctk.CTkLabel(pg_header, text="📈  Project Progress",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color="#f1f5f9").pack(side="left")

        ctk.CTkFrame(self.progress_panel, fg_color="#1e293b", height=1).pack(fill="x", padx=20)
        self.progress_list = ctk.CTkFrame(self.progress_panel, fg_color="transparent")
        self.progress_list.pack(fill="both", padx=20, pady=(12, 18))

        # Recent Activity Panel
        self.activity_panel = ctk.CTkFrame(bottom, fg_color="#111827", corner_radius=16, border_width=1, border_color="#1e293b")
        self.activity_panel.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=(0, 10))

        ac_header = ctk.CTkFrame(self.activity_panel, fg_color="transparent")
        ac_header.pack(fill="x", padx=20, pady=(18, 12))
        ctk.CTkLabel(ac_header, text="⚡  Recent Activity",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color="#f1f5f9").pack(side="left")

        ctk.CTkFrame(self.activity_panel, fg_color="#1e293b", height=1).pack(fill="x", padx=20)
        self.activity_list = ctk.CTkFrame(self.activity_panel, fg_color="transparent")
        self.activity_list.pack(fill="both", padx=20, pady=(12, 18))

    def _create_stat_card(self, parent, col, stat):
        """Create a premium stat card with icon, value, and label."""
        card = ctk.CTkFrame(parent, fg_color="#111827", corner_radius=14,
                           height=130, border_width=1, border_color="#1e293b")
        card.grid(row=0, column=col, sticky="nsew", padx=6, pady=4)
        card.pack_propagate(False)

        # Top row: icon + label
        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=18, pady=(16, 0))

        icon_bg = ctk.CTkFrame(top, fg_color=stat["accent"], corner_radius=10, width=36, height=36)
        icon_bg.pack(side="left")
        icon_bg.pack_propagate(False)
        ctk.CTkLabel(icon_bg, text=stat["icon"], font=ctk.CTkFont(size=16)).pack(expand=True)

        ctk.CTkLabel(top, text=stat["label"], font=ctk.CTkFont(size=12),
                     text_color="#64748b").pack(side="right")

        # Value
        val_lbl = ctk.CTkLabel(card, text="—", font=ctk.CTkFont(size=28, weight="bold"),
                               text_color=stat["color"])
        val_lbl.pack(anchor="w", padx=18, pady=(10, 0))

        return val_lbl

    def load_data(self):
        try:
            # Project counts
            projects = execute_query(
                "SELECT COUNT(*) as total, "
                "SUM(CASE WHEN status='active' THEN 1 ELSE 0 END) as active, "
                "SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) as completed "
                "FROM projects")
            p = projects[0] if projects else {'total': 0, 'active': 0, 'completed': 0}

            # Financial
            investments = execute_query("SELECT COALESCE(SUM(amount), 0) as total FROM investments WHERE status='confirmed'")
            budget = execute_query("SELECT COALESCE(SUM(total_budget), 0) as total FROM projects")
            investors = execute_query("SELECT COUNT(*) as total FROM investors WHERE is_active=1")
            overdue = execute_query("SELECT COUNT(*) as total FROM payment_schedules WHERE status='overdue' OR (status='pending' AND due_date < NOW())")

            # Update stat cards
            self.stat_cards[0].configure(text=str(p.get('total', 0) or 0))
            self.stat_cards[1].configure(text=f"৳ {float(investments[0].get('total', 0) or 0):,.0f}")
            self.stat_cards[2].configure(text=f"৳ {float(budget[0].get('total', 0) or 0):,.0f}")
            self.stat_cards[3].configure(text=str(investors[0].get('total', 0) or 0))
            self.stat_cards[4].configure(text=str(overdue[0].get('total', 0) or 0))
            self.stat_cards[5].configure(text=str(p.get('active', 0) or 0))

            # --- Project progress ---
            active_projects = execute_query(
                "SELECT name, progress FROM projects WHERE status='active' ORDER BY progress DESC LIMIT 8")
            for widget in self.progress_list.winfo_children():
                widget.destroy()

            if active_projects:
                for proj in active_projects:
                    row = ctk.CTkFrame(self.progress_list, fg_color="transparent")
                    row.pack(fill="x", pady=4)
                    ctk.CTkLabel(row, text=proj['name'], font=ctk.CTkFont(size=13),
                                text_color="#e2e8f0", width=180, anchor="w").pack(side="left")
                    progress = float(proj.get('progress', 0) or 0)
                    bar = ctk.CTkProgressBar(row, width=140, height=10, corner_radius=5,
                                            fg_color="#1e293b", progress_color="#3b82f6")
                    bar.set(progress / 100)
                    bar.pack(side="left", padx=(10, 8))
                    pct_color = "#10b981" if progress >= 75 else "#f59e0b" if progress >= 40 else "#94a3b8"
                    ctk.CTkLabel(row, text=f"{progress:.0f}%", font=ctk.CTkFont(size=12, weight="bold"),
                                text_color=pct_color, width=45).pack(side="left")
            else:
                ctk.CTkLabel(self.progress_list, text="No active projects yet",
                            text_color="#475569", font=ctk.CTkFont(size=13)).pack(pady=20)

            # --- Recent activity ---
            activities = execute_query(
                "SELECT a.action, a.description, a.created_at, u.username "
                "FROM audit_logs a LEFT JOIN users u ON a.user_id = u.id "
                "ORDER BY a.created_at DESC LIMIT 10")
            for widget in self.activity_list.winfo_children():
                widget.destroy()

            if activities:
                for act in activities:
                    row = ctk.CTkFrame(self.activity_list, fg_color="#0f172a", corner_radius=8)
                    row.pack(fill="x", pady=3)
                    color_map = {'create': '#10b981', 'update': '#3b82f6', 'delete': '#ef4444', 'login': '#8b5cf6'}
                    dot_color = color_map.get(act['action'], '#64748b')
                    ctk.CTkLabel(row, text="●", text_color=dot_color, font=ctk.CTkFont(size=10),
                                width=20).pack(side="left", padx=(10, 0))
                    desc = (act.get('description', '') or '')[:50]
                    ctk.CTkLabel(row, text=desc, font=ctk.CTkFont(size=12),
                                text_color="#cbd5e1", anchor="w").pack(side="left", padx=6, fill="x", expand=True)
                    time_str = format_date(act.get('created_at'), fmt="%H:%M", default="")
                    ctk.CTkLabel(row, text=time_str, font=ctk.CTkFont(size=11),
                                text_color="#475569", width=50).pack(side="right", padx=10)
            else:
                ctk.CTkLabel(self.activity_list, text="No activity yet",
                            text_color="#475569", font=ctk.CTkFont(size=13)).pack(pady=20)

        except Exception as e:
            print(f"Dashboard load error: {e}")
