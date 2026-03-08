"""
Settings View for CMS Desktop App.
Configure application settings and currency exchange rates.
"""

import customtkinter as ctk
from tkinter import messagebox
from core.database import execute_query


class SettingsView(ctk.CTkFrame):
    def __init__(self, parent, user):
        super().__init__(parent, fg_color="transparent")
        self.user = user
        self.build_ui()
        self.load_data()

    def build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header, text="Settings", font=ctk.CTkFont(size=26, weight="bold"),
                    text_color="white").pack(side="left")

        # Tabs
        self.tab_view = ctk.CTkTabview(self, fg_color="#111827", segmented_button_fg_color="#1e293b",
                                       segmented_button_selected_color="#3b82f6", corner_radius=12)
        self.tab_view.pack(fill="both", expand=True)
        self.tab_view.add("General")
        self.tab_view.add("Financial")
        self.tab_view.add("Currencies")
        self.tab_view.add("Email")

    def load_data(self):
        try:
            settings = execute_query("SELECT `key`, value, category, description FROM settings")
            self.settings_map = {s['key']: s for s in settings}
        except:
            self.settings_map = {}

        # General tab
        general = self.tab_view.tab("General")
        for key in ['company_name', 'company_email', 'company_phone', 'company_address']:
            s = self.settings_map.get(key, {})
            self._add_setting_row(general, key, s.get('value', ''), s.get('description', ''))

        # Financial tab
        financial = self.tab_view.tab("Financial")
        for key in ['base_currency', 'tax_rate', 'fiscal_year_start']:
            s = self.settings_map.get(key, {})
            self._add_setting_row(financial, key, s.get('value', ''), s.get('description', ''))

        # Email tab
        email = self.tab_view.tab("Email")
        for key in ['email_notifications', 'auto_email_on_investment', 'payment_reminder_days']:
            s = self.settings_map.get(key, {})
            self._add_setting_row(email, key, s.get('value', ''), s.get('description', ''))

        info = ctk.CTkFrame(email, fg_color="#1e3a5f", corner_radius=8)
        info.pack(fill="x", padx=20, pady=(20, 10))
        ctk.CTkLabel(info, text="💡 Configure Gmail SMTP credentials in the .env file:\n   GMAIL_USER=your-email@gmail.com\n   GMAIL_APP_PASSWORD=your-app-password",
                    font=ctk.CTkFont(size=12), text_color="#93c5fd", wraplength=500, justify="left").pack(padx=15, pady=10)

        # Currencies tab
        currencies_frame = self.tab_view.tab("Currencies")
        try:
            currencies = execute_query("SELECT * FROM currencies ORDER BY code")
        except:
            currencies = []

        ctk.CTkLabel(currencies_frame, text="Exchange Rates (relative to BDT)",
                    font=ctk.CTkFont(size=14, weight="bold"), text_color="#94a3b8").pack(anchor="w", padx=20, pady=(10, 10))

        self.rate_entries = {}
        for c in currencies:
            row = ctk.CTkFrame(currencies_frame, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=3)
            ctk.CTkLabel(row, text=f"{c['symbol']}  {c['code']} — {c['name']}",
                        font=ctk.CTkFont(size=13), text_color="#e2e8f0", width=250, anchor="w").pack(side="left")
            entry = ctk.CTkEntry(row, width=130, height=32, fg_color="#1e293b", border_color="#334155",
                               corner_radius=6)
            entry.insert(0, str(c['exchange_rate_to_base']))
            entry.pack(side="left", padx=10)
            self.rate_entries[c['id']] = entry

            if c.get('is_base'):
                ctk.CTkLabel(row, text="BASE", font=ctk.CTkFont(size=10, weight="bold"),
                            text_color="#10b981").pack(side="left")
            else:
                ctk.CTkButton(row, text="Save", width=50, height=28, corner_radius=6,
                             fg_color="#3b82f6", hover_color="#2563eb", font=ctk.CTkFont(size=11),
                             command=lambda cid=c['id']: self._save_rate(cid)).pack(side="left", padx=5)

    def _add_setting_row(self, parent, key, value, description):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=20, pady=5)

        label_text = key.replace('_', ' ').title()
        ctk.CTkLabel(frame, text=label_text, font=ctk.CTkFont(size=13, weight="bold"),
                    text_color="#e2e8f0", width=180, anchor="w").pack(side="left")

        entry = ctk.CTkEntry(frame, height=34, fg_color="#1e293b", border_color="#334155",
                            corner_radius=8, width=250)
        entry.insert(0, value)
        entry.pack(side="left", padx=10)

        ctk.CTkButton(frame, text="Save", width=55, height=30, corner_radius=6,
                     fg_color="#3b82f6", hover_color="#2563eb", font=ctk.CTkFont(size=11),
                     command=lambda k=key, e=entry: self._save_setting(k, e)).pack(side="left")

        if description:
            ctk.CTkLabel(frame, text=description, font=ctk.CTkFont(size=11),
                        text_color="#475569", wraplength=200).pack(side="left", padx=(10, 0))

    def _save_setting(self, key, entry):
        try:
            value = entry.get()
            exists = execute_query("SELECT id FROM settings WHERE `key` = %s", (key,))
            if exists:
                execute_query("UPDATE settings SET value=%s, updated_at=NOW() WHERE `key`=%s", (value, key), fetch=False)
            else:
                execute_query("INSERT INTO settings (`key`, value, created_at, updated_at) VALUES (%s, %s, NOW(), NOW())", (key, value), fetch=False)
            messagebox.showinfo("Saved", f"{key.replace('_', ' ').title()} updated!")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _save_rate(self, currency_id):
        try:
            rate = float(self.rate_entries[currency_id].get())
            execute_query("UPDATE currencies SET exchange_rate_to_base=%s, updated_at=NOW() WHERE id=%s",
                         (rate, currency_id), fetch=False)
            messagebox.showinfo("Saved", "Exchange rate updated!")
        except Exception as e:
            messagebox.showerror("Error", str(e))
