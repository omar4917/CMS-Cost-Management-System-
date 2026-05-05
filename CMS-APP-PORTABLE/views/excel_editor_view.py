"""
Excel Editor View for CMS Desktop App.
Allows users to view, edit, and re-import Excel cost trackers directly inside the app.
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog, ttk
import pandas as pd
import os
from core.database import execute_query, execute_many
from core.desktop_utils import format_date

class ExcelEditorView(ctk.CTkFrame):
    def __init__(self, parent, user):
        super().__init__(parent, fg_color="transparent")
        self.user = user
        self.df = None
        self.file_path = None
        self.build_ui()

    def build_ui(self):
        # Toolbar
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", pady=(0, 20))

        ctk.CTkButton(toolbar, text="📂 Open Excel", command=self.load_excel, 
                     fg_color="#1e293b", hover_color="#334155", width=120).pack(side="left", padx=(0, 10))
        
        self.save_btn = ctk.CTkButton(toolbar, text="💾 Save Changes", command=self.save_excel, 
                                     fg_color="#3b82f6", hover_color="#2563eb", width=120, state="disabled")
        self.save_btn.pack(side="left", padx=10)

        self.import_btn = ctk.CTkButton(toolbar, text="🚀 Save & Import to DB", command=self.import_to_db, 
                                       fg_color="#10b981", hover_color="#059669", width=160, state="disabled")
        self.import_btn.pack(side="left", padx=10)

        ctk.CTkLabel(toolbar, text="Sheet: Details Cost", font=ctk.CTkFont(size=12, slant="italic"), text_color="#64748b").pack(side="right")

        # Table Container
        self.table_container = ctk.CTkFrame(self, fg_color="#111827", corner_radius=12, border_width=1, border_color="#1e293b")
        self.table_container.pack(fill="both", expand=True)

        self.placeholder = ctk.CTkLabel(self.table_container, text="No Excel file loaded.\nClick 'Open Excel' to start editing.", 
                                       font=ctk.CTkFont(size=14), text_color="#475569")
        self.placeholder.pack(expand=True)

    def load_excel(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx")])
        if not file_path: return

        try:
            xls = pd.ExcelFile(file_path)
            if "Details Cost" not in xls.sheet_names:
                messagebox.showerror("Error", "Sheet 'Details Cost' not found in this file.")
                return
            
            # Read with header at row 2 (0-indexed)
            self.df = pd.read_excel(xls, sheet_name="Details Cost", header=2)
            self.file_path = file_path
            
            self._render_table()
            self.save_btn.configure(state="normal")
            self.import_btn.configure(state="normal")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load Excel: {e}")

    def _render_table(self):
        for w in self.table_container.winfo_children():
            w.destroy()

        if self.df is None: return

        # Scrollbars
        v_scroll = ctk.CTkScrollbar(self.table_container, orientation="vertical")
        v_scroll.pack(side="right", fill="y")
        
        h_scroll = ctk.CTkScrollbar(self.table_container, orientation="horizontal")
        h_scroll.pack(side="bottom", fill="x")

        # Style
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Excel.Treeview", background="#111827", foreground="#e2e8f0", fieldbackground="#111827", borderwidth=0, rowheight=30)
        style.map("Excel.Treeview", background=[('selected', '#1e3a8a')])
        
        self.tree = ttk.Treeview(self.table_container, columns=list(range(len(self.df.columns))), 
                                show="headings", style="Excel.Treeview", 
                                yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        for i, col in enumerate(self.df.columns):
            self.tree.heading(i, text=str(col))
            self.tree.column(i, width=120)
            
        for _, row in self.df.iterrows():
            vals = [str(v) if pd.notna(v) else "" for v in row]
            self.tree.insert("", "end", values=vals)
            
        self.tree.pack(fill="both", expand=True)
        v_scroll.configure(command=self.tree.yview)
        h_scroll.configure(command=self.tree.xview)
        
        self.tree.bind("<Double-1>", self.on_double_click)

    def on_double_click(self, event):
        item = self.tree.identify_item(event.y)
        column = self.tree.identify_column(event.x)
        if not item or not column: return
        
        col_idx = int(column.replace("#", "")) - 1
        current_val = self.tree.item(item)['values'][col_idx]
        
        # Simple entry popup
        x, y, w, h = self.tree.bbox(item, column)
        
        entry = ctk.CTkEntry(self.tree, width=w, height=h, fg_color="#1e293b", border_width=1)
        entry.insert(0, current_val)
        entry.place(x=x, y=y)
        entry.focus_set()
        
        def save_edit(event=None):
            new_val = entry.get()
            # Update Treeview
            vals = list(self.tree.item(item)['values'])
            vals[col_idx] = new_val
            self.tree.item(item, values=vals)
            # Update Dataframe
            row_idx = self.tree.index(item)
            self.df.iloc[row_idx, col_idx] = new_val
            entry.destroy()
            
        entry.bind("<Return>", save_edit)
        entry.bind("<FocusOut>", lambda e: entry.destroy())

    def save_excel(self):
        if self.df is None: return
        try:
            # We need to preserve the original structure (headers at row 3)
            # This is tricky with simple to_excel. We'll try to update the existing file if possible.
            with pd.ExcelWriter(self.file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                # We skip row 0 and 1 in the actual sheet? 
                # Better: just save to a new file to be safe
                pass
            
            save_path = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile=os.path.basename(self.file_path))
            if not save_path: return
            
            # Simple save (won't preserve original 2-row banner exactly, but good for data)
            self.df.to_excel(save_path, sheet_name="Details Cost", index=False, startrow=2)
            messagebox.showinfo("Success", "Excel saved successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save Excel: {e}")

    def import_to_db(self):
        if self.df is None: return
        
        # We need a project selection
        from views.datahub_view import DataHubView
        # Since we don't want to instantiate the whole DataHubView, we'll use its logic
        
        # For simplicity, let's just use the logic here
        project_name = messagebox.askquestion("Import", "This will import the current data into the database. Proceed?")
        if project_name != 'yes': return
        
        # Logic to map df to DB (similar to datahub_view.py)
        # ... (I'll implement a simplified version or reuse the existing logic if I can refactor it)
        # Actually, let's just trigger the import logic from here.
        messagebox.showinfo("Note", "Import logic triggered. (Connecting to project mapping...)")
        
        # I'll need to ask the user WHICH project this belongs to
        projects = execute_query("SELECT id, name FROM projects")
        if not projects:
            messagebox.showerror("Error", "No projects found in database.")
            return
            
        p_names = [p['name'] for p in projects]
        
        def _perform_import(selected_project):
            p_id = next(p['id'] for p in projects if p['name'] == selected_project)
            # Use the dataframe to build rows
            # (Reuse logic from datahub_view.py)
            self._process_df_to_db(p_id)
            
        # Simplified project picker
        picker = ctk.CTkToplevel(self)
        picker.title("Select Project for Import")
        picker.geometry("400x200")
        picker.grab_set()
        
        ctk.CTkLabel(picker, text="Which project does this data belong to?").pack(pady=20)
        p_var = ctk.StringVar(value=p_names[0])
        ctk.CTkOptionMenu(picker, variable=p_var, values=p_names).pack(pady=10)
        ctk.CTkButton(picker, text="Confirm Import", command=lambda: [picker.destroy(), _perform_import(p_var.get())]).pack(pady=10)

    def _process_df_to_db(self, project_id):
        try:
            # Replace NaNs
            df_clean = self.df.where(pd.notnull(self.df), None)
            
            def _to_float(v):
                try: return float(str(v).replace(',', '')) if v else 0.0
                except: return 0.0

            rows = []
            for _, row in df_clean.iterrows():
                # Map columns (assuming standard template headers)
                payload = (
                    project_id,
                    str(row.get("Receive DATE", "")),
                    str(row.get("Receive DETAIL", "")),
                    _to_float(row.get("Receive AMOUNT")),
                    str(row.get("Cost DATE", "")),
                    str(row.get("Cost DETAIL", "")),
                    _to_float(row.get("Cost AMOUNT")),
                    str(row.get("PAY TO", "")),
                    self.user.get('id')
                )
                rows.append(payload)
                
            if rows:
                execute_many(
                    "INSERT INTO cost_items (project_id, receive_date, receive_detail, receive_amount, cost_date, cost_detail, cost_amount, pay_to, created_by) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", rows
                )
                messagebox.showinfo("Success", f"Imported {len(rows)} items into database.")
            else:
                messagebox.showwarning("Warning", "No valid rows found to import.")
        except Exception as e:
            messagebox.showerror("Error", f"Import failed: {e}")
