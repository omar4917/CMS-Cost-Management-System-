"""
Login View for CMS Desktop App.
Modern entry screen with connection status and server setup.
"""

import os
import sys
from tkinter import messagebox

import customtkinter as ctk
from dotenv import set_key

import core.database
from core.auth import verify_login
from core.database import test_connection


class LoginView(ctk.CTkFrame):
    def __init__(self, parent, on_login_success):
        super().__init__(parent, fg_color="#07111f")
        self.parent = parent
        self.on_login_success = on_login_success
        self.build_ui()

    def build_ui(self):
        panel = ctk.CTkFrame(self, fg_color="transparent")
        panel.pack(fill="both", expand=True, padx=34, pady=34)

        left = ctk.CTkFrame(
            panel,
            fg_color="#091427",
            corner_radius=30,
            border_width=1,
            border_color="#1d2d49",
        )
        left.pack(side="left", fill="both", expand=True, padx=(0, 16))

        right = ctk.CTkFrame(
            panel,
            fg_color="#0b1327",
            corner_radius=30,
            border_width=1,
            border_color="#1d2d49",
            width=470,
        )
        right.pack(side="left", fill="y")
        right.pack_propagate(False)

        self._build_brand_panel(left)
        self._build_login_panel(right)

    def _build_brand_panel(self, parent):
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", padx=28, pady=(28, 12))

        ctk.CTkButton(
            header,
            text="Server Setup",
            height=38,
            width=118,
            corner_radius=10,
            fg_color="#162748",
            hover_color="#223863",
            command=self.open_env_settings,
        ).pack(side="right")

        chip = ctk.CTkFrame(parent, fg_color="#4f8cff", width=70, height=70, corner_radius=22)
        chip.pack(anchor="w", padx=28, pady=(24, 12))
        chip.pack_propagate(False)
        ctk.CTkLabel(chip, text="HC", font=ctk.CTkFont(size=24, weight="bold"), text_color="#f8fafc").pack(expand=True)

        ctk.CTkLabel(parent, text="Houzez CMS Desktop", font=ctk.CTkFont(size=34, weight="bold"), text_color="#f8fafc").pack(
            anchor="w", padx=28
        )
        ctk.CTkLabel(
            parent,
            text="A desktop workspace for projects, payments, contractors, investors, and AI-assisted data operations.",
            font=ctk.CTkFont(size=14),
            text_color="#7f93b7",
            wraplength=520,
            justify="left",
        ).pack(anchor="w", padx=28, pady=(10, 18))

        strip = ctk.CTkFrame(parent, fg_color="transparent")
        strip.pack(fill="x", padx=28, pady=(0, 18))
        for title, copy in [
            ("Shared database", "Point every desktop user to one MySQL backend."),
            ("Offline fallback", "Switch to local SQLite when you need portable mode."),
            ("Actionable AI", "Use natural language to seed, update, and clean data."),
        ]:
            card = ctk.CTkFrame(
                strip,
                fg_color="#0f1d36",
                corner_radius=18,
                border_width=1,
                border_color="#1d2d49",
            )
            card.pack(fill="x", pady=6)
            ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=14, weight="bold"), text_color="#f8fafc").pack(
                anchor="w", padx=16, pady=(14, 4)
            )
            ctk.CTkLabel(card, text=copy, font=ctk.CTkFont(size=12), text_color="#7f93b7").pack(
                anchor="w", padx=16, pady=(0, 14)
            )

    def _build_login_panel(self, parent):
        ctk.CTkLabel(parent, text="Admin sign-in", font=ctk.CTkFont(size=28, weight="bold"), text_color="#f8fafc").pack(
            anchor="w", padx=34, pady=(34, 6)
        )
        ctk.CTkLabel(
            parent,
            text="Use your desktop credentials to enter the control surface.",
            font=ctk.CTkFont(size=13),
            text_color="#7f93b7",
        ).pack(anchor="w", padx=34)

        self.db_status = ctk.CTkLabel(parent, text="", font=ctk.CTkFont(size=12, weight="bold"))
        self.db_status.pack(anchor="w", padx=34, pady=(18, 4))

        self.error_label = ctk.CTkLabel(parent, text="", text_color="#ff7a90", font=ctk.CTkFont(size=12), wraplength=380)
        self.error_label.pack(anchor="w", padx=34, pady=(0, 10))

        form = ctk.CTkFrame(parent, fg_color="transparent")
        form.pack(fill="x", padx=34, pady=(12, 0))

        ctk.CTkLabel(form, text="Username", font=ctk.CTkFont(size=12, weight="bold"), text_color="#9bb0d5").pack(
            anchor="w", pady=(0, 4)
        )
        self.username_entry = ctk.CTkEntry(
            form,
            height=44,
            corner_radius=12,
            placeholder_text="admin",
            fg_color="#101b35",
            border_color="#233154",
        )
        self.username_entry.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(form, text="Password", font=ctk.CTkFont(size=12, weight="bold"), text_color="#9bb0d5").pack(
            anchor="w", pady=(0, 4)
        )
        self.password_entry = ctk.CTkEntry(
            form,
            height=44,
            corner_radius=12,
            placeholder_text="Enter your password",
            show="*",
            fg_color="#101b35",
            border_color="#233154",
        )
        self.password_entry.pack(fill="x", pady=(0, 20))

        self.login_btn = ctk.CTkButton(
            form,
            text="Enter Workspace",
            height=46,
            corner_radius=12,
            fg_color="#4f8cff",
            hover_color="#3578f6",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.handle_login,
        )
        self.login_btn.pack(fill="x")

        ctk.CTkLabel(
            parent,
            text="Default desktop admin: admin / admin123",
            font=ctk.CTkFont(size=11),
            text_color="#5f759d",
        ).pack(anchor="w", padx=34, pady=(12, 0))

        self.password_entry.bind("<Return>", lambda _event: self.handle_login())
        self.username_entry.bind("<Return>", lambda _event: self.password_entry.focus())

        self.check_db()

    def check_db(self):
        conn_type = os.environ.get("DB_TYPE", "mysql").lower()
        ok, message = test_connection()
        if ok:
            if conn_type == "sqlite":
                self.db_status.configure(text="Connected: Local SQLite workspace", text_color="#27d3a2")
            else:
                host = os.environ.get("DB_HOST", "localhost")
                self.db_status.configure(text=f"Connected: MySQL on {host}", text_color="#27d3a2")
        else:
            self.db_status.configure(text=f"Database error: {message[:70]}", text_color="#ff7a90")

    def handle_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            self.error_label.configure(text="Enter both username and password.")
            return

        self.login_btn.configure(state="disabled", text="Signing in...")
        self.error_label.configure(text="")
        self.update_idletasks()

        try:
            user, error = verify_login(username, password)
            if user:
                self.on_login_success(user)
                return
            self.error_label.configure(text=error or "Login failed.")
        except Exception as exc:
            self.error_label.configure(text=f"Connection error: {str(exc)[:90]}")
        finally:
            self.login_btn.configure(state="normal", text="Enter Workspace")

    def open_env_settings(self):
        if getattr(sys, "frozen", False):
            app_dir = os.path.dirname(sys.executable)
        else:
            app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env_path = os.path.join(app_dir, ".env")

        dialog = ctk.CTkToplevel(self)
        dialog.title("Server Setup")
        dialog.geometry("540x560")
        dialog.configure(fg_color="#0b1327")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Server Setup", font=ctk.CTkFont(size=24, weight="bold"), text_color="#f8fafc").pack(
            pady=(24, 6)
        )
        ctk.CTkLabel(
            dialog,
            text="Point the desktop app to a shared MySQL database or switch to local offline mode.",
            font=ctk.CTkFont(size=12),
            text_color="#7f93b7",
            wraplength=430,
        ).pack()

        form = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=30, pady=(18, 0))

        sqlite_var = ctk.BooleanVar(value=os.environ.get("DB_TYPE", "mysql").lower() == "sqlite")
        ctk.CTkSwitch(
            form,
            text="Use Local SQLite (Offline Mode)",
            variable=sqlite_var,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#9bb0d5",
        ).pack(anchor="w", pady=(0, 14))

        mysql_frame = ctk.CTkFrame(form, fg_color="transparent")
        mysql_frame.pack(fill="x", expand=True)

        fields = {}

        def add_field(label, key, default=""):
            ctk.CTkLabel(mysql_frame, text=label, font=ctk.CTkFont(size=12, weight="bold"), text_color="#9bb0d5").pack(
                anchor="w", pady=(8, 4)
            )
            entry = ctk.CTkEntry(
                mysql_frame,
                height=40,
                fg_color="#101b35",
                border_color="#233154",
                corner_radius=10,
            )
            entry.insert(0, os.environ.get(key, default))
            entry.pack(fill="x")
            fields[key] = entry

        add_field("Database Host", "DB_HOST", "127.0.0.1")
        add_field("Database User", "DB_USER", "root")

        ctk.CTkLabel(mysql_frame, text="Database Password", font=ctk.CTkFont(size=12, weight="bold"), text_color="#9bb0d5").pack(
            anchor="w", pady=(8, 4)
        )
        pwd_entry = ctk.CTkEntry(
            mysql_frame,
            height=40,
            fg_color="#101b35",
            border_color="#233154",
            corner_radius=10,
            show="*",
        )
        pwd_entry.insert(0, os.environ.get("DB_PASS", os.environ.get("DB_PASSWORD", "")))
        pwd_entry.pack(fill="x")
        fields["DB_PASS"] = pwd_entry

        add_field("Database Name", "DB_NAME", "cms_db")
        add_field("Database Port", "DB_PORT", "3306")

        def toggle_fields(*_args):
            state = "disabled" if sqlite_var.get() else "normal"
            for widget in mysql_frame.winfo_children():
                try:
                    widget.configure(state=state)
                except Exception:
                    pass

        sqlite_var.trace_add("write", toggle_fields)
        toggle_fields()

        def save_env():
            try:
                if not os.path.exists(env_path):
                    open(env_path, "a", encoding="utf-8").close()

                db_type = "sqlite" if sqlite_var.get() else "mysql"
                os.environ["DB_TYPE"] = db_type
                set_key(env_path, "DB_TYPE", db_type)

                for key, entry in fields.items():
                    value = entry.get().strip()
                    os.environ[key] = value
                    set_key(env_path, key, value)

                core.database.DB_TYPE = db_type
                core.database._pool = None
                core.database._sqlite_initialized = False
                core.database._table_columns_cache = {}

                dialog.destroy()
                self.check_db()
                messagebox.showinfo("Saved", "Database settings saved and the connection cache was reset.")
            except Exception as exc:
                messagebox.showerror("Error", f"Failed to save settings: {exc}")

        footer = ctk.CTkFrame(dialog, fg_color="transparent")
        footer.pack(fill="x", padx=30, pady=(10, 24))
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
            text="Save & Reconnect",
            fg_color="#4f8cff",
            hover_color="#3578f6",
            corner_radius=10,
            height=38,
            command=save_env,
        ).pack(side="right")
