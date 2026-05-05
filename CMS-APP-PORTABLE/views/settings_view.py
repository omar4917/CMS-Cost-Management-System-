"""
Settings view for the desktop app.
"""

import os
import sys
from tkinter import messagebox

import bcrypt
import customtkinter as ctk
from dotenv import set_key

from core.database import execute_query
from core.desktop_utils import pick_column


if getattr(sys, "frozen", False):
    app_dir = os.path.dirname(sys.executable)
else:
    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(app_dir, ".env")


class SettingsView(ctk.CTkFrame):
    def __init__(self, parent, user):
        super().__init__(parent, fg_color="transparent")
        self.user = user
        self.setting_key_col = pick_column("settings", "key", "setting_key", fallback="setting_key")
        self.setting_value_col = pick_column("settings", "value", "setting_value", fallback="setting_value")
        self.setting_desc_col = pick_column("settings", "description", fallback=None)
        self.build_ui()
        self.load_data()

    def build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header, text="Settings", font=ctk.CTkFont(size=26, weight="bold"), text_color="white").pack(side="left")

        self.tab_view = ctk.CTkTabview(
            self,
            fg_color="#111827",
            segmented_button_fg_color="#1e293b",
            segmented_button_selected_color="#3b82f6",
            corner_radius=12,
        )
        self.tab_view.pack(fill="both", expand=True)
        for tab_name in ["General", "Financial", "Currencies", "Email", "Users & Admins", "Environment (.env)"]:
            self.tab_view.add(tab_name)

    def load_data(self):
        for name in ["General", "Financial", "Currencies", "Email", "Users & Admins", "Environment (.env)"]:
            self._clear_tab(self.tab_view.tab(name))

        self.settings_map = self._load_settings_map()
        self._load_general_tab()
        self._load_financial_tab()
        self._load_currencies_tab()
        self._load_email_tab()
        self._load_users_tab()
        self._load_environment_tab()

    def _clear_tab(self, tab):
        for widget in tab.winfo_children():
            widget.destroy()

    def _load_settings_map(self):
        select_parts = [
            f"{self.setting_key_col} AS setting_key",
            f"{self.setting_value_col} AS setting_value",
            "category",
        ]
        if self.setting_desc_col:
            select_parts.append(f"{self.setting_desc_col} AS description")
        else:
            select_parts.append("NULL AS description")
        try:
            rows = execute_query(f"SELECT {', '.join(select_parts)} FROM settings")
            return {row["setting_key"]: row for row in rows}
        except Exception:
            return {}

    def _load_general_tab(self):
        tab = self.tab_view.tab("General")
        for key in ["company_name", "company_email", "company_phone", "company_address"]:
            item = self.settings_map.get(key, {})
            self._add_setting_row(tab, key, item.get("setting_value", ""), item.get("description", ""))

    def _load_financial_tab(self):
        tab = self.tab_view.tab("Financial")
        for key in ["base_currency", "tax_rate", "fiscal_year_start"]:
            item = self.settings_map.get(key, {})
            self._add_setting_row(tab, key, item.get("setting_value", ""), item.get("description", ""))

    def _load_email_tab(self):
        tab = self.tab_view.tab("Email")
        for key in ["email_notifications", "auto_email_on_investment", "payment_reminder_days"]:
            item = self.settings_map.get(key, {})
            self._add_setting_row(tab, key, item.get("setting_value", ""), item.get("description", ""))

        info = ctk.CTkFrame(tab, fg_color="#1e3a5f", corner_radius=8)
        info.pack(fill="x", padx=20, pady=(20, 10))
        ctk.CTkLabel(
            info,
            text="Configure Gmail SMTP credentials in the .env file:\nGMAIL_USER=your-email@gmail.com\nGMAIL_APP_PASS=your-app-password",
            font=ctk.CTkFont(size=12),
            text_color="#93c5fd",
            wraplength=500,
            justify="left",
        ).pack(padx=15, pady=10)

    def _load_currencies_tab(self):
        tab = self.tab_view.tab("Currencies")
        ctk.CTkLabel(tab, text="Exchange Rates (relative to BDT)", font=ctk.CTkFont(size=14, weight="bold"), text_color="#94a3b8").pack(anchor="w", padx=20, pady=(10, 10))
        self.rate_entries = {}
        try:
            currencies = execute_query("SELECT * FROM currencies ORDER BY code")
        except Exception:
            currencies = []

        for currency in currencies:
            row = ctk.CTkFrame(tab, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=3)
            ctk.CTkLabel(row, text=f"{currency.get('symbol') or ''}  {currency['code']} - {currency.get('name') or ''}", font=ctk.CTkFont(size=13), text_color="#e2e8f0", width=250, anchor="w").pack(side="left")
            entry = ctk.CTkEntry(row, width=130, height=32, fg_color="#1e293b", border_color="#334155", corner_radius=6)
            entry.insert(0, str(currency.get("exchange_rate_to_base", 1)))
            entry.pack(side="left", padx=10)
            self.rate_entries[currency["id"]] = entry
            if currency.get("is_base"):
                ctk.CTkLabel(row, text="BASE", font=ctk.CTkFont(size=10, weight="bold"), text_color="#10b981").pack(side="left")
            else:
                ctk.CTkButton(row, text="Save", width=50, height=28, corner_radius=6, fg_color="#3b82f6", hover_color="#2563eb", font=ctk.CTkFont(size=11), command=lambda currency_id=currency["id"]: self._save_rate(currency_id)).pack(side="left", padx=5)

    def _load_users_tab(self):
        tab = self.tab_view.tab("Users & Admins")
        header = ctk.CTkFrame(tab, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(16, 10))
        text_col = ctk.CTkFrame(header, fg_color="transparent")
        text_col.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(text_col, text="Desktop Users", font=ctk.CTkFont(size=18, weight="bold"), text_color="#f8fafc").pack(anchor="w")
        ctk.CTkLabel(
            text_col,
            text="Admin section for the desktop app. Database: SQLite. Portable database for local usage.",
            font=ctk.CTkFont(size=12),
            text_color="#8ea3c7",
            wraplength=760,
            justify="left",
        ).pack(anchor="w", pady=(4, 0))
        ctk.CTkButton(header, text="+ Add User", fg_color="#3b82f6", hover_color="#2563eb", corner_radius=10, height=36, command=lambda: self._open_user_dialog()).pack(side="right")

        table = ctk.CTkScrollableFrame(tab, fg_color="#0f172a", corner_radius=14, border_width=1, border_color="#1e293b")
        table.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        try:
            users = execute_query("SELECT id, username, email, first_name, last_name, role, is_active, created_at FROM users ORDER BY username ASC")
        except Exception as exc:
            ctk.CTkLabel(table, text=f"Error loading users: {exc}", text_color="#ef4444").pack(pady=20)
            return

        if not users:
            ctk.CTkLabel(table, text="No users found", font=ctk.CTkFont(size=14, weight="bold"), text_color="#64748b").pack(pady=30)
            return

        header_row = ctk.CTkFrame(table, fg_color="#101b35", corner_radius=8)
        header_row.pack(fill="x", padx=6, pady=(6, 2))
        self._configure_user_columns(header_row)
        for idx, label in enumerate(["Username", "Name", "Email", "Role", "Status", "Actions"]):
            ctk.CTkLabel(header_row, text=label.upper(), font=ctk.CTkFont(size=10, weight="bold"), text_color="#64748b", anchor="w").grid(row=0, column=idx, sticky="ew", padx=8, pady=10)

        for user in users:
            row = ctk.CTkFrame(table, fg_color="#111827", corner_radius=8)
            row.pack(fill="x", padx=6, pady=2)
            self._configure_user_columns(row)
            row.bind("<Enter>", lambda _e, r=row: r.configure(fg_color="#1e293b"))
            row.bind("<Leave>", lambda _e, r=row: r.configure(fg_color="#111827"))

            display_name = " ".join(part for part in [user.get("first_name"), user.get("last_name")] if part).strip() or "-"
            values = [
                user.get("username") or "",
                display_name,
                user.get("email") or "-",
                str(user.get("role") or "admin").title(),
                "Active" if user.get("is_active") else "Inactive",
            ]
            for idx, value in enumerate(values):
                color = "#f8fafc" if idx in {0, 4} else "#c7d2fe"
                if idx == 4:
                    color = "#10b981" if user.get("is_active") else "#ef4444"
                ctk.CTkLabel(row, text=value, font=ctk.CTkFont(size=12, weight="bold" if idx in {0, 4} else "normal"), text_color=color, anchor="w").grid(row=0, column=idx, sticky="ew", padx=8, pady=10)

            btns = ctk.CTkFrame(row, fg_color="transparent")
            btns.grid(row=0, column=5, sticky="e", padx=8, pady=8)
            ctk.CTkButton(btns, text="Edit", width=46, height=28, corner_radius=6, fg_color="#1e293b", hover_color="#334155", command=lambda item=user: self._open_user_dialog(item)).pack(side="left", padx=2)
            ctk.CTkButton(
                btns,
                text="Disable" if user.get("is_active") else "Enable",
                width=64,
                height=28,
                corner_radius=6,
                fg_color="#182748",
                hover_color="#223660",
                command=lambda item=user: self._toggle_user_active(item),
            ).pack(side="left", padx=2)
            self._bind_click(row, lambda _e, item=user: self._open_user_dialog(item))

    def _configure_user_columns(self, frame):
        specs = [(0, 1, 120), (1, 2, 180), (2, 2, 220), (3, 1, 110), (4, 1, 90), (5, 0, 140)]
        for column, weight, minsize in specs:
            frame.grid_columnconfigure(column, weight=weight, minsize=minsize)

    def _load_environment_tab(self):
        tab = self.tab_view.tab("Environment (.env)")
        ctk.CTkLabel(
            tab,
            text="Any changes marked with an asterisk (*) require restarting the app to take effect.",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#facc15",
        ).pack(anchor="w", padx=20, pady=(10, 15))

        env_vars = [
            ("AI_PROVIDER", "AI_PROVIDER", "groq"),
            ("AI_API_KEY", "AI_API_KEY", ""),
            ("GMAIL_USER", "GMAIL_USER", ""),
            ("GMAIL_APP_PASS", "GMAIL_APP_PASS", ""),
        ]
        for label_text, key, default_value in env_vars:
            self._add_env_row(tab, label_text, key, os.getenv(key, default_value))

    def _add_env_row(self, parent, label_text, key, value):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(frame, text=label_text, font=ctk.CTkFont(size=13, weight="bold"), text_color="#e2e8f0", width=180, anchor="w").pack(side="left")
        entry = ctk.CTkEntry(frame, height=34, fg_color="#1e293b", border_color="#334155", corner_radius=8, width=350)
        if "API_KEY" in key or "PASS" in key:
            entry.configure(show="*")
        entry.insert(0, value)
        entry.pack(side="left", padx=10)
        ctk.CTkButton(frame, text="Save", width=55, height=30, corner_radius=6, fg_color="#10b981", hover_color="#059669", font=ctk.CTkFont(size=11), command=lambda env_key=key, env_entry=entry: self._save_env_setting(env_key, env_entry)).pack(side="left")

    def _save_env_setting(self, key, entry):
        try:
            value = entry.get().strip()
            os.environ[key] = value
            if not os.path.exists(env_path):
                open(env_path, "a", encoding="utf-8").close()
            set_key(env_path, key, value)
            messagebox.showinfo("Saved", f"Environment variable {key} updated in .env.")
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to save {key}: {exc}")

    def _add_setting_row(self, parent, key, value, description):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(frame, text=key.replace("_", " ").title(), font=ctk.CTkFont(size=13, weight="bold"), text_color="#e2e8f0", width=180, anchor="w").pack(side="left")
        entry = ctk.CTkEntry(frame, height=34, fg_color="#1e293b", border_color="#334155", corner_radius=8, width=250)
        entry.insert(0, value)
        entry.pack(side="left", padx=10)
        ctk.CTkButton(frame, text="Save", width=55, height=30, corner_radius=6, fg_color="#3b82f6", hover_color="#2563eb", font=ctk.CTkFont(size=11), command=lambda setting_key=key, setting_entry=entry: self._save_setting(setting_key, setting_entry)).pack(side="left")
        if description:
            ctk.CTkLabel(frame, text=description, font=ctk.CTkFont(size=11), text_color="#475569", wraplength=240, justify="left").pack(side="left", padx=(10, 0))

    def _save_setting(self, key, entry):
        try:
            value = entry.get().strip()
            exists = execute_query(f"SELECT id FROM settings WHERE {self.setting_key_col}=%s", (key,))
            if exists:
                execute_query(f"UPDATE settings SET {self.setting_value_col}=?, updated_at=CURRENT_TIMESTAMP WHERE {self.setting_key_col}=?", (value, key), fetch=False)
            else:
                execute_query(f"INSERT INTO settings ({self.setting_key_col}, {self.setting_value_col}, created_at, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)", (key, value), fetch=False)
            messagebox.showinfo("Saved", f"{key.replace('_', ' ').title()} updated.")
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _save_rate(self, currency_id):
        try:
            rate = float(self.rate_entries[currency_id].get())
            execute_query("UPDATE currencies SET exchange_rate_to_base=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (rate, currency_id), fetch=False)
            messagebox.showinfo("Saved", "Exchange rate updated.")
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _open_user_dialog(self, user=None):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Edit User" if user else "Add User")
        dialog.geometry("560x640")
        dialog.configure(fg_color="#0f172a")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Edit User" if user else "Add User", font=ctk.CTkFont(size=22, weight="bold"), text_color="white").pack(pady=(20, 15))
        form = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=30)

        fields = {}

        def add_field(label, key, default="", password=False):
            ctk.CTkLabel(form, text=label, font=ctk.CTkFont(size=12, weight="bold"), text_color="#94a3b8").pack(anchor="w", pady=(10, 3))
            entry = ctk.CTkEntry(form, height=40, fg_color="#1e293b", border_color="#334155", corner_radius=10, font=ctk.CTkFont(size=13), show="*" if password else "")
            value = str(user.get(key, "") or default) if user and not password else str(default or "")
            if value:
                entry.insert(0, value)
            entry.pack(fill="x")
            fields[key] = entry

        add_field("Username *", "username")
        add_field("First Name", "first_name")
        add_field("Last Name", "last_name")
        add_field("Email", "email")

        ctk.CTkLabel(form, text="Role", font=ctk.CTkFont(size=12, weight="bold"), text_color="#94a3b8").pack(anchor="w", pady=(10, 3))
        role_var = ctk.StringVar(value=str(user.get("role") or "admin") if user else "admin")
        ctk.CTkOptionMenu(form, values=["superadmin", "admin", "manager", "finance", "viewer"], variable=role_var, fg_color="#1e293b", button_color="#334155", height=40, corner_radius=10).pack(fill="x")

        ctk.CTkLabel(form, text="Status", font=ctk.CTkFont(size=12, weight="bold"), text_color="#94a3b8").pack(anchor="w", pady=(10, 3))
        status_var = ctk.StringVar(value="Active" if not user or user.get("is_active") else "Inactive")
        ctk.CTkOptionMenu(form, values=["Active", "Inactive"], variable=status_var, fg_color="#1e293b", button_color="#334155", height=40, corner_radius=10).pack(fill="x")

        add_field("Password" + ("" if user else " *"), "password", password=True)
        add_field("Confirm Password" + ("" if user else " *"), "confirm_password", password=True)

        def save():
            username = fields["username"].get().strip()
            password = fields["password"].get().strip()
            confirm = fields["confirm_password"].get().strip()
            if not username:
                messagebox.showwarning("Validation", "Username is required.")
                return
            if user and user.get("id") == self.user.get("id") and status_var.get() == "Inactive":
                messagebox.showwarning("Validation", "You cannot deactivate the account you are currently using.")
                return
            if not user and not password:
                messagebox.showwarning("Validation", "Password is required for new users.")
                return
            if password or confirm:
                if password != confirm:
                    messagebox.showwarning("Validation", "Passwords do not match.")
                    return
                password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            else:
                password_hash = None

            base_payload = (
                username,
                fields["email"].get().strip() or None,
                fields["first_name"].get().strip() or None,
                fields["last_name"].get().strip() or None,
                role_var.get().strip() or "admin",
                1 if status_var.get() == "Active" else 0,
            )
            try:
                if user:
                    if password_hash:
                        execute_query(
                            "UPDATE users SET username=?, email=?, first_name=?, last_name=?, role=?, is_active=?, password=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                            base_payload + (password_hash, user["id"]),
                            fetch=False,
                        )
                    else:
                        execute_query(
                            "UPDATE users SET username=?, email=?, first_name=?, last_name=?, role=?, is_active=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                            base_payload + (user["id"],),
                            fetch=False,
                        )
                else:
                    execute_query(
                        "INSERT INTO users (username, email, password, first_name, last_name, role, is_active, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
                        (username, fields["email"].get().strip() or None, password_hash, fields["first_name"].get().strip() or None, fields["last_name"].get().strip() or None, role_var.get().strip() or "admin", 1 if status_var.get() == "Active" else 0),
                        fetch=False,
                    )
            except Exception as exc:
                messagebox.showerror("Error", str(exc))
                return

            dialog.destroy()
            self.load_data()

        footer = ctk.CTkFrame(dialog, fg_color="transparent")
        footer.pack(fill="x", padx=30, pady=(10, 20))
        ctk.CTkButton(footer, text="Cancel", fg_color="#1e293b", hover_color="#334155", height=40, corner_radius=10, command=dialog.destroy).pack(side="left")
        ctk.CTkButton(footer, text="Save User", fg_color="#3b82f6", hover_color="#2563eb", height=40, corner_radius=10, command=save).pack(side="right")

    def _toggle_user_active(self, user):
        if user.get("id") == self.user.get("id"):
            messagebox.showwarning("Validation", "You cannot disable the account you are currently using.")
            return
        try:
            next_state = 0 if user.get("is_active") else 1
            execute_query("UPDATE users SET is_active=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (next_state, user["id"]), fetch=False)
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
            return
        self.load_data()

    def _bind_click(self, widget, callback):
        if isinstance(widget, ctk.CTkButton):
            return
        widget.bind("<Button-1>", callback)
        for child in widget.winfo_children():
            self._bind_click(child, callback)
