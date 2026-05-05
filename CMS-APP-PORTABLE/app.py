"""
CMS Desktop App - Main Entry Point.
Standalone portable Cost Management System for real estate.
"""

import os
import sys
from datetime import datetime

import customtkinter as ctk
from dotenv import load_dotenv


if getattr(sys, "frozen", False):
    app_dir = os.path.dirname(sys.executable)
else:
    app_dir = os.path.dirname(os.path.abspath(__file__))

env_path = os.path.join(app_dir, ".env")
if not os.path.exists(env_path):
    with open(env_path, "w", encoding="utf-8") as env_file:
        env_file.write(
            "DB_HOST=127.0.0.1\n"
            "DB_USER=root\n"
            "DB_PASS=\n"
            "DB_NAME=cms_db\n"
            "DB_PORT=3306\n"
            "AI_PROVIDER=groq\n"
            "AI_API_KEY=\n"
        )

load_dotenv(env_path)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


NAV_SECTIONS = [
    (
        "OPERATIONS",
        [
            ("dashboard", "OV", "Overview", "Health & metrics"),
            ("projects", "PR", "Projects", "Pipelines & units"),
            ("costs", "CO", "Costs", "Spending & vendors"),
            ("contractors", "VN", "Contractors", "Profiles & payouts"),
        ],
    ),
    (
        "FINANCE",
        [
            ("investors", "IN", "Investors", "Profiles & exposure"),
            ("investments", "IV", "Investments", "Capital flows"),
            ("payments", "SC", "Schedules", "Installments & dues"),
            ("transactions", "TR", "Transactions", "All money movement"),
            ("reports", "RP", "Reports", "Exports & PDFs"),
        ],
    ),
    (
        "SYSTEM",
        [
            ("emails", "EM", "Email", "Outreach & templates"),
            ("ai", "AI", "Assistant", "AI data operations"),
            ("audit", "AT", "Audit", "Change history"),
            ("recycle", "RB", "Recycle", "Deleted items"),
            ("datahub", "BK", "Data Hub", "Backups & portability"),
            ("settings", "ST", "Settings", "App configuration"),
        ],
    ),
]


VIEW_META = {
    "dashboard": ("Overview", "Portfolio health, current activity, and headline metrics."),
    "projects": ("Projects", "Create, track, and clean up development pipelines."),
    "costs": ("Costs", "Control purchase records, quantities, and vendor spend."),
    "contractors": ("Contractors", "Manage external vendors and contractor payouts."),
    "investors": ("Investors", "Maintain investor profiles and commitments."),
    "investments": ("Investments", "Record investments, sales, buys, and operating cash flow."),
    "payments": ("Payment Schedules", "Watch due dates, collections, and reminders."),
    "transactions": ("Transactions", "Review every financial movement in one flow."),
    "reports": ("Reports", "Generate export-ready summaries and printouts."),
    "emails": ("Email", "Compose outreach and manage templates."),
    "ai": ("AI Assistant", "Operate the desktop app through guided prompts."),
    "audit": ("Audit Trail", "See who changed what and when."),
    "recycle": ("Recycle Bin", "Restore or purge deleted records captured by the desktop app."),
    "datahub": ("Data Hub", "Backups, transfers, and portability controls."),
    "settings": ("Settings", "Tune behavior, branding, user access, and database connections."),
}


class CMSApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Houzez CMS Desktop")
        self.geometry("1520x920")
        self.minsize(1220, 760)
        self.configure(fg_color="#07111f")

        self.current_user = None
        self.current_view = None
        self.nav_buttons = {}

        self.show_login()

    def show_login(self):
        self._clear_content()
        from views.login_view import LoginView

        self.login_frame = LoginView(self, on_login_success=self.on_login)
        self.login_frame.pack(fill="both", expand=True)

    def on_login(self, user):
        self.current_user = user
        self.login_frame.destroy()
        self._bootstrap_demo_workspace()
        self.build_main_layout()
        self.navigate("dashboard")

    def build_main_layout(self):
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=18, pady=18)

        self.sidebar = ctk.CTkFrame(
            self.main_frame,
            fg_color="#091427",
            corner_radius=28,
            border_width=1,
            border_color="#1e2d49",
            width=310,
        )
        self.sidebar.pack(side="left", fill="y", padx=(0, 16))
        self.sidebar.pack_propagate(False)

        self._build_sidebar()

        self.shell = ctk.CTkFrame(
            self.main_frame,
            fg_color="#08111f",
            corner_radius=28,
            border_width=1,
            border_color="#14243f",
        )
        self.shell.pack(side="left", fill="both", expand=True)

        self._build_shell()

    def _build_sidebar(self):
        brand = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand.pack(fill="x", padx=20, pady=(20, 16))

        icon = ctk.CTkFrame(brand, fg_color="#4f8cff", width=52, height=52, corner_radius=16)
        icon.pack(side="left")
        icon.pack_propagate(False)
        ctk.CTkLabel(icon, text="HC", text_color="#f8fafc", font=ctk.CTkFont(size=18, weight="bold")).pack(expand=True)

        copy = ctk.CTkFrame(brand, fg_color="transparent")
        copy.pack(side="left", padx=(14, 0))
        ctk.CTkLabel(copy, text="Houzez CMS", font=ctk.CTkFont(size=20, weight="bold"), text_color="#f8fafc").pack(anchor="w")
        ctk.CTkLabel(copy, text="Desktop command center", font=ctk.CTkFont(size=12), text_color="#7f93b7").pack(anchor="w", pady=(2, 0))

        ctk.CTkFrame(self.sidebar, fg_color="#162642", height=1).pack(fill="x", padx=20, pady=(0, 10))

        self.sidebar_scroll = ctk.CTkScrollableFrame(
            self.sidebar,
            fg_color="transparent",
            scrollbar_button_color="#1c2b48",
            scrollbar_button_hover_color="#27406b",
        )
        self.sidebar_scroll.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        for section_name, items in NAV_SECTIONS:
            ctk.CTkLabel(
                self.sidebar_scroll,
                text=section_name,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="#5f759d",
            ).pack(anchor="w", padx=10, pady=(14, 6))

            for key, code, label, summary in items:
                self._create_nav_button(key, code, label, summary)

        footer = ctk.CTkFrame(
            self.sidebar,
            fg_color="#0f1d36",
            corner_radius=18,
            border_width=1,
            border_color="#1d2d49",
        )
        footer.pack(fill="x", padx=16, pady=(6, 16))

        initials = (self.current_user.get("firstName", "A")[:1] or "A").upper()
        badge = ctk.CTkFrame(footer, fg_color="#1e3358", width=42, height=42, corner_radius=14)
        badge.pack(side="left", padx=14, pady=14)
        badge.pack_propagate(False)
        ctk.CTkLabel(badge, text=initials, text_color="#f8fafc", font=ctk.CTkFont(size=15, weight="bold")).pack(expand=True)

        info = ctk.CTkFrame(footer, fg_color="transparent")
        info.pack(side="left", pady=14)
        ctk.CTkLabel(
            info,
            text=self.current_user.get("firstName", "Admin"),
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#f8fafc",
        ).pack(anchor="w")
        ctk.CTkLabel(
            info,
            text=(self.current_user.get("role", "admin") or "admin").upper(),
            font=ctk.CTkFont(size=11),
            text_color="#7f93b7",
        ).pack(anchor="w", pady=(2, 0))

        ctk.CTkButton(
            footer,
            text="Logout",
            width=84,
            height=34,
            corner_radius=10,
            fg_color="#182748",
            hover_color="#243863",
            command=self.logout,
        ).pack(side="right", padx=14)

    def _build_shell(self):
        self.topbar = ctk.CTkFrame(self.shell, fg_color="transparent")
        self.topbar.pack(fill="x", padx=24, pady=(22, 10))

        title_col = ctk.CTkFrame(self.topbar, fg_color="transparent")
        title_col.pack(side="left", fill="x", expand=True)

        self.section_title = ctk.CTkLabel(
            title_col,
            text="Overview",
            font=ctk.CTkFont(size=30, weight="bold"),
            text_color="#f8fafc",
        )
        self.section_title.pack(anchor="w")
        self.section_subtitle = ctk.CTkLabel(
            title_col,
            text="",
            font=ctk.CTkFont(size=13),
            text_color="#7f93b7",
        )
        self.section_subtitle.pack(anchor="w", pady=(4, 0))

        meta = ctk.CTkFrame(self.topbar, fg_color="transparent")
        meta.pack(side="right")
        ctk.CTkLabel(
            meta,
            text=datetime.now().strftime("%d %b %Y"),
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#9ab0d8",
        ).pack(anchor="e")
        ctk.CTkLabel(
            meta,
            text="Desktop workspace",
            font=ctk.CTkFont(size=12),
            text_color="#5f759d",
        ).pack(anchor="e", pady=(2, 0))

        self.content_area = ctk.CTkFrame(
            self.shell,
            fg_color="#06101d",
            corner_radius=24,
            border_width=1,
            border_color="#14243f",
        )
        self.content_area.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    def _create_nav_button(self, key, code, label, summary):
        button = ctk.CTkButton(
            self.sidebar_scroll,
            text=f"{code}  {label}",
            fg_color="transparent",
            hover_color="#12203a",
            corner_radius=12,
            height=42,
            anchor="w",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#c8d6f1",
            command=lambda nav_key=key: self.navigate(nav_key),
        )
        button.pack(fill="x", padx=4, pady=2)
        self.nav_buttons[key] = button

    def navigate(self, view_name):
        meta = VIEW_META.get(view_name, ("Workspace", ""))
        self.section_title.configure(text=meta[0])
        self.section_subtitle.configure(text=meta[1])

        for key, button in self.nav_buttons.items():
            if key == view_name:
                button.configure(fg_color="#11203b", text_color="#f8fafc")
            else:
                button.configure(fg_color="transparent", text_color="#c8d6f1")

        if self.current_view:
            self.current_view.destroy()

        try:
            if view_name == "dashboard":
                from views.dashboard_view import DashboardView

                self.current_view = DashboardView(self.content_area, self.current_user)
            elif view_name == "projects":
                from views.projects_view import ProjectsView

                self.current_view = ProjectsView(self.content_area, self.current_user)
            elif view_name == "contractors":
                from views.contractors_view import ContractorsView

                self.current_view = ContractorsView(self.content_area, self.current_user)
            elif view_name == "investors":
                from views.investors_view import InvestorsView

                self.current_view = InvestorsView(self.content_area, self.current_user)
            elif view_name == "investments":
                from views.investments_view import InvestmentsView

                self.current_view = InvestmentsView(self.content_area, self.current_user)
            elif view_name == "costs":
                from views.costs_view import CostManagementView

                self.current_view = CostManagementView(self.content_area, self.current_user)
            elif view_name == "payments":
                from views.payments_view import PaymentSchedulesView

                self.current_view = PaymentSchedulesView(self.content_area, self.current_user)
            elif view_name == "transactions":
                from views.transactions_view import TransactionsView

                self.current_view = TransactionsView(self.content_area, self.current_user)
            elif view_name == "emails":
                from views.emails_view import EmailsView

                self.current_view = EmailsView(self.content_area, self.current_user)
            elif view_name == "reports":
                from views.reports_view import ReportsView

                self.current_view = ReportsView(self.content_area, self.current_user)
            elif view_name == "ai":
                from views.ai_assistant_view import AIAssistantView

                self.current_view = AIAssistantView(self.content_area, self.current_user)
            elif view_name == "audit":
                from views.audit_view import AuditView

                self.current_view = AuditView(self.content_area, self.current_user)
            elif view_name == "recycle":
                from views.recycle_view import RecycleBinView

                self.current_view = RecycleBinView(self.content_area, self.current_user)
            elif view_name == "datahub":
                from views.datahub_view import DataHubView

                self.current_view = DataHubView(self.content_area, self.current_user)
            elif view_name == "settings":
                from views.settings_view import SettingsView

                self.current_view = SettingsView(self.content_area, self.current_user)
            else:
                self.current_view = ctk.CTkLabel(
                    self.content_area,
                    text=f"{view_name} is not available yet.",
                    font=ctk.CTkFont(size=18),
                    text_color="#7f93b7",
                )

            self.current_view.pack(fill="both", expand=True, padx=20, pady=20)
        except Exception as exc:
            err = ctk.CTkLabel(
                self.content_area,
                text=f"Error loading {view_name}: {exc}",
                text_color="#ef4444",
                wraplength=760,
            )
            err.pack(pady=40)
            self.current_view = err

    def logout(self):
        self.current_user = None
        if hasattr(self, "main_frame"):
            self.main_frame.destroy()
        self.show_login()

    def _bootstrap_demo_workspace(self):
        try:
            from core.demo_data import seed_connected_demo_data_if_empty

            seed_connected_demo_data_if_empty(user_id=self.current_user.get("id"))
        except Exception as exc:
            print(f"Auto demo seed skipped: {exc}")

    def _clear_content(self):
        for widget in self.winfo_children():
            widget.destroy()


if __name__ == "__main__":
    app = CMSApp()
    app.mainloop()
