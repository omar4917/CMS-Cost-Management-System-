"""
Data Hub View for CMS Desktop App.
Handles backups, Excel transfers, and connected desktop demo data generation.
"""

import os
import threading
from datetime import datetime
from tkinter import filedialog, messagebox

import customtkinter as ctk
import pandas as pd

from core import ai_service
from core.database import DB_CONFIG, execute_many, execute_query
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
            text="Export All Data",
            fg_color="#1e293b",
            hover_color="#334155",
            command=self.export_excel,
            width=140,
            height=40,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_row1,
            text="Export Cost Tracker",
            fg_color="#10b981",
            hover_color="#059669",
            command=self.export_cost_tracker,
            width=160,
            height=40,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_row1,
            text="Import (AI)",
            fg_color="#1e293b",
            hover_color="#334155",
            command=self.import_excel,
            width=100,
            height=40,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_row1,
            text="Import Cost Tracker",
            fg_color="#8b5cf6",
            hover_color="#7c3aed",
            command=self.import_cost_tracker,
            width=160,
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
            text="Currently running on: SQLite",
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

        ctk.CTkButton(
            btn_row2,
            text="Clear Database",
            fg_color="#ef4444",
            hover_color="#dc2626",
            command=self.clear_database,
            width=200,
            height=40,
        ).pack(side="left")

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

    def export_cost_tracker(self):
        try:
            project_choice = self._prompt_project_for_costs(title="Export Cost Tracker", allow_all=True, allow_none=True)
            if project_choice is None:
                return
            project_id, project_name = project_choice
            safe_project = "".join(ch for ch in (project_name or "") if ch.isalnum() or ch in (" ", "_", "-")).strip().replace(" ", "_")

            save_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                initialfile=(
                    f"Cost_Tracker_{safe_project}_{datetime.now().strftime('%Y%m%d')}.xlsx"
                    if safe_project
                    else f"Cost_Tracker_Export_{datetime.now().strftime('%Y%m%d')}.xlsx"
                ),
                title="Save Exact Cost Tracker Template",
                filetypes=[("Excel Files", "*.xlsx")],
            )
            if not save_path:
                return

            if project_id is None:
                items = execute_query("SELECT * FROM cost_items ORDER BY id ASC")
            else:
                items = execute_query("SELECT * FROM cost_items WHERE project_id=%s ORDER BY id ASC", (project_id,))
            
            headers = [
                "Receive DATE", "Receive DETAIL", "Receive AMOUNT", "RECEIVED FROM",
                "Cost DATE", "Cost DETAIL", "Cost AMOUNT", "PAY TO",
                "Unit", "Unit Rate", "Qty", "Qty (CFT)", "REMARKS",
                "COST HEAD (Materials)", "Structure/Finishing", "Cost Summary 1",
                "Category BOQ Mapping", "COST HEAD (Floors)", "COST HEAD (Project & Office)", "COST HEAD (Months)"
            ]

            # Look up extra field labels for this project
            extra_labels = {}  # {field_key: label}
            if project_id is not None:
                try:
                    label_rows = execute_query(
                        "SELECT field_key, label FROM custom_field_labels WHERE project_id=%s ORDER BY sort_order",
                        (project_id,),
                    )
                    extra_labels = {r["field_key"]: r["label"] for r in (label_rows or [])}
                except Exception:
                    pass
            else:
                # "All Projects" — collect union of all extra labels
                try:
                    label_rows = execute_query(
                        "SELECT DISTINCT field_key, label FROM custom_field_labels ORDER BY sort_order",
                    )
                    extra_labels = {r["field_key"]: r["label"] for r in (label_rows or [])}
                except Exception:
                    pass

            # Build ordered list of extra keys that have labels
            extra_keys = [f"extra_{i}" for i in range(1, 11) if f"extra_{i}" in extra_labels]
            for ek in extra_keys:
                headers.append(extra_labels[ek])
            
            # Use openpyxl directly to build the exact template structure
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
            
            wb = Workbook()
            ws = wb.active
            ws.title = "Details Cost"
            
            # Row 1: Summary Banner (Calculated with formulas below data later, or dynamic)
            # We will write this at the end to know the last row
            
            # Row 2: Sub-headers (mostly empty in original, but required for alignment)
            
            # Row 3: Headers
            header_font = Font(bold=True, color="FFFFFF")
            header_fill = PatternFill(start_color="334155", end_color="334155", fill_type="solid")
            for col_idx, text in enumerate(headers, start=1):
                cell = ws.cell(row=3, column=col_idx, value=text)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

            # Data Rows
            start_row = 4
            for r_idx, item in enumerate(items, start=start_row):
                row_data = [
                    item.get("receive_date"), item.get("receive_detail"), item.get("receive_amount") or 0, item.get("received_from"),
                    item.get("cost_date"), item.get("cost_detail"), item.get("cost_amount") or 0, item.get("pay_to"),
                    item.get("unit"), item.get("unit_rate") or 0, item.get("qty") or 0, item.get("qty_cft") or 0, item.get("remarks"),
                    item.get("cost_head_materials"), item.get("structure_or_finishing"), item.get("cost_summary_1"),
                    item.get("category_boq_mapping"), item.get("cost_head_floors"), item.get("cost_head_project"), item.get("cost_head_months")
                ]
                # Append extra field values
                for ek in extra_keys:
                    row_data.append(item.get(ek))

                for c_idx, val in enumerate(row_data, start=1):
                    ws.cell(row=r_idx, column=c_idx, value=val)
                # Auto-calculate Cost AMOUNT if Unit Rate and Qty exist
                ws.cell(row=r_idx, column=7).value = f"=J{r_idx}*K{r_idx}"

            last_row = max(start_row, len(items) + start_row - 1)
            
            # Top Summary
            ws.cell(row=1, column=1, value="TOTAL RECEIVE").font = Font(bold=True)
            ws.cell(row=1, column=2, value=f"=SUM(C{start_row}:C{last_row})").font = Font(bold=True)
            ws.cell(row=1, column=4, value="IN HAND").font = Font(bold=True)
            ws.cell(row=1, column=5, value="=B1-F1").font = Font(bold=True)
            ws.cell(row=1, column=6, value="TOTAL EXPENDITURE").font = Font(bold=True)
            ws.cell(row=1, column=7, value=f"=SUM(G{start_row}:G{last_row})").font = Font(bold=True)

            wb.save(save_path)
            messagebox.showinfo("Success", f"Cost Tracker successfully exported to Excel.\n{save_path}")
            os.startfile(os.path.dirname(save_path))

            execute_query(
                "INSERT INTO audit_logs (user_id, action, entity_type, description) VALUES (%s, %s, %s, %s)",
                (
                    self.user.get("id"),
                    "EXPORT",
                    "cost_tracker",
                    f"Exported Cost Tracker template to Excel (project={project_name if project_name else 'NONE'})",
                ),
                fetch=False,
            )
        except Exception as exc:
            messagebox.showerror("Export Failed", str(exc))

    def _prompt_project_for_costs(self, *, title: str, allow_all: bool, allow_none: bool):
        try:
            projects = execute_query("SELECT id, name FROM projects ORDER BY name") or []
        except Exception:
            projects = []

        options = []
        if allow_all:
            options.append("(All Projects)")
        if allow_none:
            options.append("(No Project)")
        options += [f"{p['id']} | {p['name']}" for p in projects]
        options.append("+ Create new project...")

        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("520x360")
        dialog.configure(fg_color="#0b1327")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        ctk.CTkLabel(dialog, text=title, font=ctk.CTkFont(size=20, weight="bold"), text_color="#f8fafc").pack(
            pady=(22, 8)
        )
        ctk.CTkLabel(
            dialog,
            text="Choose the project for these cost rows, or create a new project.",
            font=ctk.CTkFont(size=12),
            text_color="#7f93b7",
            wraplength=430,
        ).pack(pady=(0, 16))

        var = ctk.StringVar(value=options[0] if options else "+ Create new project...")
        menu = ctk.CTkOptionMenu(
            dialog,
            values=options or ["+ Create new project..."],
            variable=var,
            fg_color="#101b35",
            button_color="#233154",
            height=40,
            width=420,
        )
        menu.pack(pady=(0, 10))

        new_name = ctk.CTkEntry(
            dialog,
            height=38,
            fg_color="#101b35",
            border_color="#233154",
            corner_radius=10,
            placeholder_text="New project name",
            width=420,
        )

        def sync():
            if var.get() == "+ Create new project...":
                new_name.pack(pady=(6, 0))
            else:
                try:
                    new_name.pack_forget()
                except Exception:
                    pass

        var.trace_add("write", lambda *_: sync())
        sync()

        result = {"ok": False, "project_id": None, "project_name": None}

        def on_cancel():
            dialog.destroy()

        def on_ok():
            choice = var.get()
            if choice == "(All Projects)":
                result.update({"ok": True, "project_id": None, "project_name": "ALL"})
                dialog.destroy()
                return
            if choice == "(No Project)":
                result.update({"ok": True, "project_id": None, "project_name": ""})
                dialog.destroy()
                return
            if choice == "+ Create new project...":
                name = (new_name.get() or "").strip()
                if not name:
                    messagebox.showwarning("Validation", "Enter a project name.")
                    return
                try:
                    project_id = execute_query(
                        "INSERT INTO projects (name, created_by, created_at, updated_at) VALUES (%s, %s, NOW(), NOW())",
                        (name, self.user.get("id")),
                        fetch=False,
                    )
                except Exception as exc:
                    messagebox.showerror("Error", str(exc))
                    return
                result.update({"ok": True, "project_id": int(project_id), "project_name": name})
                dialog.destroy()
                return

            try:
                project_id = int(str(choice).split("|", 1)[0].strip())
                project_name = str(choice).split("|", 1)[1].strip()
                result.update({"ok": True, "project_id": project_id, "project_name": project_name})
                dialog.destroy()
            except Exception:
                messagebox.showwarning("Validation", "Select a valid project.")

        footer = ctk.CTkFrame(dialog, fg_color="transparent")
        footer.pack(fill="x", padx=30, pady=(18, 22))
        ctk.CTkButton(footer, text="Cancel", fg_color="#182748", hover_color="#223660", height=38, command=on_cancel).pack(
            side="left"
        )
        ctk.CTkButton(footer, text="Continue", fg_color="#4f8cff", hover_color="#3578f6", height=38, command=on_ok).pack(
            side="right"
        )

        dialog.wait_window()
        if not result["ok"]:
            return None
        return result["project_id"], result["project_name"]

    def import_cost_tracker(self):
        file_path = filedialog.askopenfilename(
            title="Select Cost Tracker Excel File",
            filetypes=[("Excel Files", "*.xlsx *.xls")],
        )
        if not file_path:
            return

        # Import must be tied to a project (existing or newly created) so the ledger is meaningful.
        project_choice = self._prompt_project_for_costs(title="Import Cost Tracker", allow_all=False, allow_none=False)
        if project_choice is None:
            return
        project_id, project_name = project_choice

        self.import_status.configure(text="Reading Cost Tracker...", text_color="#f59e0b")
        self.update_idletasks()

        def _process():
            try:
                # Direct parse logic
                import pandas as pd
                xls = pd.ExcelFile(file_path)
                if "Details Cost" not in xls.sheet_names:
                    raise ValueError("Sheet 'Details Cost' not found. Please select a valid Cost Tracker template.")
                
                # We skip row 1 and 2, headers are at row 3 (index 2)
                df = pd.read_excel(xls, sheet_name="Details Cost", header=2)
                
                required_cols = ["Receive DATE", "Receive AMOUNT", "Cost DATE", "Cost DETAIL", "Cost AMOUNT", "PAY TO"]
                missing = [c for c in required_cols if c not in df.columns]
                if missing:
                    # Fallback to AI diagnostic
                    self.after(0, lambda: self.import_status.configure(text="Template structure missing. Running AI diagnostic...", text_color="#f59e0b"))
                    prompt = (
                        f"The user tried to import an Excel file as the Cost Tracker template, but it's missing expected columns: {missing}.\n"
                        f"Here is the first 10 rows of the provided Excel data:\n{df.head(10).to_csv(index=False)}\n\n"
                        "Diagnose why this doesn't match the template. Provide a short, bulleted explanation to show the user what needs fixing."
                    )
                    response = ai_service.chat([{"role": "user", "content": prompt}])
                    self.after(0, lambda: messagebox.showerror("Template Parsing Failed", f"The AI analyzed your file and found issues:\n\n{response}"))
                    self.after(0, lambda: self.import_status.configure(text="Import failed.", text_color="#ef4444"))
                    return

                # It matches! Parse it.
                self.after(0, lambda: self.import_status.configure(text="Parsing data into database...", text_color="#f59e0b"))
                
                # Replace NaNs with None
                df = df.where(pd.notnull(df), None)

                def _to_text(value):
                    if value is None:
                        return None
                    try:
                        if pd.isna(value):
                            return None
                    except Exception:
                        pass
                    text = str(value).strip()
                    if not text or text.lower() == "nan":
                        return None
                    return text

                def _to_float(value):
                    try:
                        if value is None or value == "":
                            return 0.0
                        try:
                            if pd.isna(value):
                                return 0.0
                        except Exception:
                            pass
                        if isinstance(value, str):
                            cleaned = value.strip().replace(",", "")
                            return float(cleaned) if cleaned else 0.0
                        return float(value)
                    except (TypeError, ValueError):
                        return 0.0

                def _to_date(value):
                    if value is None or value == "":
                        return None
                    try:
                        if pd.isna(value):
                            return None
                    except Exception:
                        pass
                    try:
                        if isinstance(value, pd.Timestamp):
                            return value.date().isoformat()
                    except Exception:
                        pass
                    text = str(value).strip()
                    if not text or text.lower() == "nan":
                        return None
                    # Normalize "YYYY-MM-DD HH:MM:SS" -> "YYYY-MM-DD"
                    if " " in text:
                        text = text.split(" ", 1)[0]
                    return text

                # --- Detect extra columns beyond the standard template ---
                KNOWN_COLUMNS = {
                    "Receive DATE", "Receive DETAIL", "Receive AMOUNT", "RECEIVED FROM",
                    "Cost DATE", "Cost DETAIL", "Cost AMOUNT", "PAY TO",
                    "Unit", "Unit Rate", "Qty", "Qty (CFT)", "REMARKS",
                    "COST HEAD (Materials)", "Structure/Finishing", "Cost Summary 1",
                    "Category BOQ Mapping", "COST HEAD (Floors)", "COST HEAD (Project & Office)", "COST HEAD (Months)",
                }
                extra_excel_cols = [c for c in df.columns if c not in KNOWN_COLUMNS and not str(c).startswith("Unnamed")]
                extra_excel_cols = extra_excel_cols[:10]  # Cap at 10 extra fields

                # Save extra column labels for this project
                if extra_excel_cols and project_id is not None:
                    # Clear existing labels for this project first
                    execute_query(
                        "DELETE FROM custom_field_labels WHERE project_id=%s",
                        (project_id,),
                        fetch=False,
                    )
                    for idx, col_name in enumerate(extra_excel_cols):
                        execute_query(
                            "INSERT INTO custom_field_labels (project_id, field_key, label, sort_order) VALUES (%s, %s, %s, %s)",
                            (project_id, f"extra_{idx + 1}", str(col_name), idx),
                            fetch=False,
                        )

                rows = []
                for _, row in df.iterrows():
                    cost_detail = _to_text(row.get("Cost DETAIL"))
                    receive_detail = _to_text(row.get("Receive DETAIL"))

                    # Skip empty rows (after header)
                    if not cost_detail and not receive_detail:
                        continue

                    unit_rate = _to_float(row.get("Unit Rate"))
                    qty = _to_float(row.get("Qty"))
                    cost_amount = _to_float(row.get("Cost AMOUNT"))
                    if cost_amount == 0 and unit_rate > 0 and qty > 0:
                        cost_amount = unit_rate * qty

                    # Build extra values (always 10 slots)
                    extra_values = []
                    for idx in range(10):
                        if idx < len(extra_excel_cols):
                            extra_values.append(_to_text(row.get(extra_excel_cols[idx])))
                        else:
                            extra_values.append(None)

                    payload = (
                        project_id,
                        _to_date(row.get("Receive DATE")),
                        receive_detail,
                        _to_float(row.get("Receive AMOUNT")),
                        _to_text(row.get("RECEIVED FROM")),
                        _to_date(row.get("Cost DATE")),
                        cost_detail,
                        cost_amount,
                        _to_text(row.get("PAY TO")),
                        _to_text(row.get("Unit")),
                        unit_rate,
                        qty,
                        _to_float(row.get("Qty (CFT)")),
                        _to_text(row.get("REMARKS")),
                        _to_text(row.get("COST HEAD (Materials)")),
                        _to_text(row.get("Structure/Finishing")),
                        _to_text(row.get("Cost Summary 1")),
                        _to_text(row.get("Category BOQ Mapping")),
                        _to_text(row.get("COST HEAD (Floors)")),
                        _to_text(row.get("COST HEAD (Project & Office)")),
                        _to_text(row.get("COST HEAD (Months)")),
                        *extra_values,
                        self.user.get("id"),
                    )
                    rows.append(payload)

                if rows:
                    count = execute_many(
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
                            created_by
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        rows,
                    )
                else:
                    count = 0

                extra_msg = f" (+{len(extra_excel_cols)} extra fields)" if extra_excel_cols else ""
                self.after(
                    0,
                    lambda: self.import_status.configure(
                        text=f"Import complete. Added {count} cost items.{extra_msg}",
                        text_color="#10b981",
                    ),
                )

                execute_query(
                    "INSERT INTO audit_logs (user_id, action, entity_type, description) VALUES (%s, %s, %s, %s)",
                    (
                        self.user.get("id"),
                        "IMPORT",
                        "cost_tracker",
                        f"Imported {count} cost tracker rows from Excel (project={project_name or 'NONE'}, extras={len(extra_excel_cols)})",
                    ),
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

        import threading
        threading.Thread(target=_process, daemon=True).start()

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
                "recycle_bin",
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

            save_path = filedialog.asksaveasfilename(
                defaultextension=".sqlite",
                initialfile=f"cms_sqlite_backup_{timestamp}.sqlite",
                title="Save Database Backup",
            )
            if not save_path:
                return

            import shutil
            import sys
            if getattr(sys, 'frozen', False):
                app_dir = os.path.dirname(sys.executable)
            else:
                app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(app_dir, "cms_data.db")
            
            if os.path.exists(db_path):
                shutil.copy2(db_path, save_path)
                messagebox.showinfo("Success", f"SQLite database successfully backed up to:\n{save_path}")
            else:
                messagebox.showwarning("Warning", "Database file not found.")

            execute_query(
                "INSERT INTO audit_logs (user_id, action, entity_type, description) VALUES (%s, %s, %s, %s)",
                (self.user.get("id"), "BACKUP", "database", "Triggered database backup"),
                fetch=False,
            )
        except Exception as exc:
            messagebox.showerror("Backup Failed", str(exc))

    def clear_database(self):
        yes = messagebox.askyesno(
            "Clear Database",
            "This will permanently delete ALL records from the SQLite database and then restore the default seed data (admin user, categories, templates, currencies).\n\nProceed?",
        )
        if not yes:
            return

        self.import_status.configure(text="Clearing database...", text_color="#f59e0b")
        self.update_idletasks()

        def _process():
            try:
                from core.database import clear_database as clear_db

                clear_db()

                execute_query(
                    "INSERT INTO audit_logs (user_id, action, entity_type, description) VALUES (%s, %s, %s, %s)",
                    (self.user.get("id"), "CLEAR", "database", "Cleared SQLite database from Data Hub"),
                    fetch=False,
                )

                self.after(
                    0,
                    lambda: self.import_status.configure(
                        text="Database cleared and defaults restored.",
                        text_color="#10b981",
                    ),
                )
            except Exception as exc:
                self.after(
                    0,
                    lambda: self.import_status.configure(
                        text=f"Clear failed: {str(exc)[:70]}",
                        text_color="#ef4444",
                    ),
                )

        threading.Thread(target=_process, daemon=True).start()

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
