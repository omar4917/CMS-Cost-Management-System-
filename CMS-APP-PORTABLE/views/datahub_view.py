"""
Data Hub View for CMS Desktop App.
Handles backups, Excel transfers, and connected desktop demo data generation.
"""

import os
import shutil
import threading
from datetime import datetime
from tkinter import filedialog, messagebox

import customtkinter as ctk
import pandas as pd

from core import ai_service
from core.database import DB_CONFIG, DB_TYPE, execute_query
from core.demo_data import seed_connected_demo_data


class DataHubView(ctk.CTkFrame):
    def __init__(self, parent, user):
        super().__init__(parent, fg_color="transparent")
        self.user = user
        self.build_ui()

    def build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(
            header,
            text="Data & Backup Hub",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color="white",
        ).pack(side="left")

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)

        excel_card = ctk.CTkFrame(self.container, fg_color="#111827", corner_radius=12)
        excel_card.pack(fill="x", pady=10)
        ctk.CTkLabel(
            excel_card,
            text="Excel Import / Export (AI Assisted)",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="white",
        ).pack(anchor="w", padx=20, pady=(15, 5))
        ctk.CTkLabel(
            excel_card,
            text="Export the desktop database to a multi-sheet Excel file, or upload an Excel file and let the AI map rows into the correct tables.",
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8",
            wraplength=800,
            justify="left",
        ).pack(anchor="w", padx=20, pady=(0, 15))

        btn_row1 = ctk.CTkFrame(excel_card, fg_color="transparent")
        btn_row1.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkButton(
            btn_row1,
            text="Export All to Excel",
            fg_color="#10b981",
            hover_color="#059669",
            command=self.export_excel,
            width=200,
            height=40,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_row1,
            text="Import from Excel (AI)",
            fg_color="#8b5cf6",
            hover_color="#7c3aed",
            command=self.import_excel,
            width=200,
            height=40,
        ).pack(side="left")

        self.import_status = ctk.CTkLabel(
            btn_row1,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="#3b82f6",
        )
        self.import_status.pack(side="left", padx=15)

        db_card = ctk.CTkFrame(self.container, fg_color="#111827", corner_radius=12)
        db_card.pack(fill="x", pady=10)
        ctk.CTkLabel(
            db_card,
            text="Database Backup & Restore",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="white",
        ).pack(anchor="w", padx=20, pady=(15, 5))
        ctk.CTkLabel(
            db_card,
            text=f"Currently running on: {DB_TYPE.upper()}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#3b82f6",
        ).pack(anchor="w", padx=20, pady=(0, 5))
        ctk.CTkLabel(
            db_card,
            text="Generate a physical backup file of the desktop database.",
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8",
        ).pack(anchor="w", padx=20, pady=(0, 15))

        btn_row2 = ctk.CTkFrame(db_card, fg_color="transparent")
        btn_row2.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkButton(
            btn_row2,
            text="Backup Database",
            fg_color="#3b82f6",
            hover_color="#2563eb",
            command=self.backup_database,
            width=200,
            height=40,
        ).pack(side="left", padx=(0, 10))

        demo_card = ctk.CTkFrame(self.container, fg_color="#111827", corner_radius=12)
        demo_card.pack(fill="x", pady=10)
        ctk.CTkLabel(
            demo_card,
            text="Connected Demo Workspace",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="white",
        ).pack(anchor="w", padx=20, pady=(15, 5))
        ctk.CTkLabel(
            demo_card,
            text="Create linked desktop test data across Projects, Costs, Contractors, Investors, Transactions, Payment Schedules, Email, Audit, Dashboard, and Reports.",
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8",
            wraplength=820,
            justify="left",
        ).pack(anchor="w", padx=20, pady=(0, 15))

        btn_row3 = ctk.CTkFrame(demo_card, fg_color="transparent")
        btn_row3.pack(fill="x", padx=20, pady=(0, 15))

        self.demo_seed_button = ctk.CTkButton(
            btn_row3,
            text="Generate Connected Demo Data",
            fg_color="#f59e0b",
            hover_color="#d97706",
            command=self.seed_demo_workspace,
            width=240,
            height=40,
        )
        self.demo_seed_button.pack(side="left", padx=(0, 10))

        self.demo_status = ctk.CTkLabel(
            btn_row3,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="#3b82f6",
        )
        self.demo_status.pack(side="left", padx=15)

    def export_excel(self):
        try:
            save_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                initialfile=f"CMS_Export_{datetime.now().strftime('%Y%m%d')}.xlsx",
                title="Save Excel Export",
                filetypes=[("Excel Files", "*.xlsx")],
            )
            if not save_path:
                return

            tables = [
                "projects",
                "cost_categories",
                "cost_items",
                "investor_types",
                "investors",
                "investments",
                "payment_schedules",
                "contractors",
                "contractor_payments",
                "cash_transactions",
                "email_templates",
                "email_logs",
                "audit_logs",
            ]

            with pd.ExcelWriter(save_path, engine="openpyxl") as writer:
                for table in tables:
                    try:
                        data = execute_query(f"SELECT * FROM {table}")
                        if data:
                            df = pd.DataFrame(data)
                            for col in df.select_dtypes(include=["datetime64[ns]", "datetime64[ns, UTC]", "datetime"]).columns:
                                df[col] = df[col].dt.tz_localize(None)
                            df.to_excel(writer, sheet_name=table, index=False)
                    except Exception as exc:
                        print(f"Skipping table {table}: {exc}")

            messagebox.showinfo("Success", f"Database successfully exported to Excel.\n{save_path}")
            os.startfile(os.path.dirname(save_path))

            execute_query(
                "INSERT INTO audit_logs (user_id, action, entity_type, description) VALUES (%s, %s, %s, %s)",
                (self.user.get("id"), "EXPORT", "database", "Exported database to Excel"),
                fetch=False,
            )
        except Exception as exc:
            messagebox.showerror("Export Failed", str(exc))

    def import_excel(self):
        file_path = filedialog.askopenfilename(
            title="Select Excel File for AI Import",
            filetypes=[("Excel Files", "*.xlsx *.xls")],
        )
        if not file_path:
            return

        yes = messagebox.askyesno(
            "Confirm AI Import",
            "The AI will read the Excel file and generate database records for the desktop app based on the contents.\n\nThis may take a minute. Proceed?",
        )
        if not yes:
            return

        self.import_status.configure(text="Reading Excel file...", text_color="#f59e0b")
        self.update_idletasks()

        def _process():
            try:
                xls = pd.ExcelFile(file_path)
                data_str = ""
                for sheet in xls.sheet_names:
                    df = pd.read_excel(xls, sheet_name=sheet).head(50)
                    if not df.empty:
                        data_str += f"\n--- SHEET: {sheet} ---\n"
                        data_str += df.to_csv(index=False)

                self.after(
                    0,
                    lambda: self.import_status.configure(
                        text="AI is analyzing data and generating records...",
                        text_color="#f59e0b",
                    ),
                )

                prompt = (
                    "I am providing tabular data extracted from an Excel file uploaded by the user.\n"
                    "Your job is to parse this data and execute JSON actions to INSERT the data into the correct tables "
                    "(for example projects, cost_items, investors, investments, and payment_schedules).\n"
                    "IMPORTANT: Output only the JSON blocks needed to insert the data. Map the columns as best as you can.\n"
                    f"EXCEL DATA:\n{data_str}"
                )

                response = ai_service.chat([{"role": "user", "content": prompt}])

                import json

                blocks = re.findall(r"```json\s*(.*?)\s*```", response, re.DOTALL)
                count = 0
                for block in blocks:
                    try:
                        data = json.loads(block)
                        if data.get("execute_action") == "insert":
                            table = data["table"]
                            payload = data["data"]
                            cols = ", ".join(payload.keys())
                            holders = ", ".join(["%s"] * len(payload))
                            query = f"INSERT INTO {table} ({cols}) VALUES ({holders})"
                            execute_query(query, tuple(payload.values()), fetch=False)
                            count += 1
                    except Exception as exc:
                        print("AI Action Error:", exc)

                self.after(
                    0,
                    lambda: self.import_status.configure(
                        text=f"Import complete. Added {count} records.",
                        text_color="#10b981",
                    ),
                )

                execute_query(
                    "INSERT INTO audit_logs (user_id, action, entity_type, description) VALUES (%s, %s, %s, %s)",
                    (self.user.get("id"), "IMPORT", "excel", f"AI imported {count} records from Excel"),
                    fetch=False,
                )
            except Exception as exc:
                self.after(
                    0,
                    lambda: self.import_status.configure(
                        text=f"Import failed: {str(exc)[:70]}",
                        text_color="#ef4444",
                    ),
                )

        import re

        threading.Thread(target=_process, daemon=True).start()

    def backup_database(self):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")

            if DB_TYPE == "sqlite":
                import sys

                if getattr(sys, "frozen", False):
                    app_dir = os.path.dirname(sys.executable)
                else:
                    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

                db_path = os.path.join(app_dir, os.getenv("DB_FILE", "cms_local.db"))

                if not os.path.exists(db_path):
                    return messagebox.showerror("Error", "SQLite database file not found.")

                save_path = filedialog.asksaveasfilename(
                    defaultextension=".db",
                    initialfile=f"cms_backup_{timestamp}.db",
                    title="Save Database Backup",
                )
                if not save_path:
                    return

                shutil.copy2(db_path, save_path)
                messagebox.showinfo("Success", f"SQLite database successfully backed up to:\n{save_path}")
            else:
                save_path = filedialog.asksaveasfilename(
                    defaultextension=".sql",
                    initialfile=f"cms_mysql_backup_{timestamp}.sql",
                    title="Save Database Backup",
                )
                if not save_path:
                    return

                host = DB_CONFIG.get("host", "localhost")
                user = DB_CONFIG.get("user", "root")
                pwd = DB_CONFIG.get("password", "")
                db = DB_CONFIG.get("database", "cms_db")
                port = DB_CONFIG.get("port", 3306)

                cmd = f'mysqldump -h {host} -P {port} -u {user} '
                if pwd:
                    cmd += f'-p"{pwd}" '
                cmd += f'{db} > "{save_path}"'

                result = os.system(cmd)
                if result == 0:
                    messagebox.showinfo("Success", f"MySQL database successfully backed up to:\n{save_path}")
                else:
                    messagebox.showwarning(
                        "Warning",
                        "mysqldump failed. Make sure MySQL tools are installed and added to your system PATH.",
                    )

            execute_query(
                "INSERT INTO audit_logs (user_id, action, entity_type, description) VALUES (%s, %s, %s, %s)",
                (self.user.get("id"), "BACKUP", "database", "Triggered database backup"),
                fetch=False,
            )
        except Exception as exc:
            messagebox.showerror("Backup Failed", str(exc))

    def seed_demo_workspace(self):
        yes = messagebox.askyesno(
            "Generate Connected Demo Data",
            "This will create a new connected demo batch for the desktop app across projects, finance, email, and audit tables.\n\nProceed?",
        )
        if not yes:
            return

        self.demo_seed_button.configure(state="disabled")
        self.demo_status.configure(text="Generating linked demo records...", text_color="#f59e0b")

        def _process():
            try:
                total, summary = seed_connected_demo_data(user_id=self.user.get("id"))

                def _success():
                    self.demo_seed_button.configure(state="normal")
                    self.demo_status.configure(
                        text=f"Created {total} linked records.",
                        text_color="#10b981",
                    )
                    messagebox.showinfo(
                        "Demo Data Ready",
                        f"Connected desktop demo data created successfully.\n\n{summary}\n\nTotal records: {total}",
                    )

                self.after(0, _success)
            except Exception as exc:
                def _error():
                    self.demo_seed_button.configure(state="normal")
                    self.demo_status.configure(
                        text=f"Failed: {str(exc)[:70]}",
                        text_color="#ef4444",
                    )
                    messagebox.showerror("Demo Data Failed", str(exc))

                self.after(0, _error)

        threading.Thread(target=_process, daemon=True).start()
