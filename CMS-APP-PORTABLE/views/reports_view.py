"""
Reports View for CMS Desktop App.
Generates PDF summaries of Projects, Costs, and Investor Statements.
"""

import os
import customtkinter as ctk
from tkinter import messagebox, filedialog
from core.database import execute_query
from core.desktop_utils import format_date
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime

class ReportsView(ctk.CTkFrame):
    def __init__(self, parent, user):
        super().__init__(parent, fg_color="transparent")
        self.user = user
        self.build_ui()
        self.load_data()

    def build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header, text="Reports & PDFs", font=ctk.CTkFont(size=26, weight="bold"),
                    text_color="white").pack(side="left")

        # Container
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)

        # Generate Project Cost PDF
        p_card = ctk.CTkFrame(self.container, fg_color="#111827", corner_radius=12)
        p_card.pack(fill="x", pady=10)
        ctk.CTkLabel(p_card, text="Project Cost Breakdown Report", font=ctk.CTkFont(size=16, weight="bold"), text_color="white").pack(anchor="w", padx=20, pady=(15, 5))
        ctk.CTkLabel(p_card, text="Generate a detailed PDF of all costs and materials associated with a project.", font=ctk.CTkFont(size=12), text_color="#94a3b8").pack(anchor="w", padx=20, pady=(0, 15))
        
        row1 = ctk.CTkFrame(p_card, fg_color="transparent")
        row1.pack(fill="x", padx=20, pady=(0, 15))
        self.proj_var = ctk.StringVar(value="Select Project")
        ctk.CTkOptionMenu(row1, variable=self.proj_var, values=[], fg_color="#1e293b", width=300).pack(side="left")
        ctk.CTkButton(row1, text="⬇️ Download PDF", fg_color="#ef4444", hover_color="#dc2626", command=self.generate_project_pdf).pack(side="left", padx=10)

        # Generate Investor Statement PDF
        i_card = ctk.CTkFrame(self.container, fg_color="#111827", corner_radius=12)
        i_card.pack(fill="x", pady=10)
        ctk.CTkLabel(i_card, text="Investor Financial Statement", font=ctk.CTkFont(size=16, weight="bold"), text_color="white").pack(anchor="w", padx=20, pady=(15, 5))
        ctk.CTkLabel(i_card, text="Generate a PDF showing an investor's total investments, schedules, and balances.", font=ctk.CTkFont(size=12), text_color="#94a3b8").pack(anchor="w", padx=20, pady=(0, 15))
        
        row2 = ctk.CTkFrame(i_card, fg_color="transparent")
        row2.pack(fill="x", padx=20, pady=(0, 15))
        self.inv_var = ctk.StringVar(value="Select Investor")
        ctk.CTkOptionMenu(row2, variable=self.inv_var, values=[], fg_color="#1e293b", width=300).pack(side="left")
        ctk.CTkButton(row2, text="⬇️ Download PDF", fg_color="#ef4444", hover_color="#dc2626", command=self.generate_investor_pdf).pack(side="left", padx=10)

    def load_data(self):
        try:
            projs = execute_query("SELECT id, name FROM projects")
            invs = execute_query("SELECT id, name FROM investors")
            
            p_opts = [f"{p['name']} (ID: {p['id']})" for p in projs]
            i_opts = [f"{i['name']} (ID: {i['id']})" for i in invs]
            
            if p_opts:
                self.proj_var.set(p_opts[0])
                self.container.winfo_children()[0].winfo_children()[2].winfo_children()[0].configure(values=p_opts)
            if i_opts:
                self.inv_var.set(i_opts[0])
                self.container.winfo_children()[1].winfo_children()[2].winfo_children()[0].configure(values=i_opts)
        except Exception as e:
            print("Error loading data for reports:", e)

    def generate_project_pdf(self):
        val = self.proj_var.get()
        if not 'ID:' in val: return messagebox.showerror("Error", "Select a project first")
        p_id = val.split('ID: ')[1].replace(')', '')
        
        save_path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=f"Project_Cost_Report_{p_id}.pdf", title="Save Project Report")
        if not save_path: return

        try:
            proj = execute_query("SELECT * FROM projects WHERE id=%s", (p_id,))[0]
            costs = execute_query(
                "SELECT cost_detail as name, cost_amount as actual_amount, cost_date as date, cost_head_materials as cat_name "
                "FROM cost_items WHERE cost_head_project=%s ORDER BY cost_date DESC", 
                (proj['name'],)
            )
            
            doc = SimpleDocTemplate(save_path, pagesize=letter)
            styles = getSampleStyleSheet()
            elements = []
            
            elements.append(Paragraph(f"CMS Cost Breakdown Report", styles['Title']))
            elements.append(Paragraph(f"Project: {proj['name']} (Budget: ৳{float(proj['total_budget'] or 0):,.0f})", styles['Heading2']))
            elements.append(Spacer(1, 20))
            
            data = [["Date", "Category", "Item / Material", "Amount (৳)"]]
            total = 0
            for c in costs:
                amt = float(c['actual_amount'] or 0)
                total += amt
                data.append([format_date(c['date'], default='N/A'), c['cat_name'] or '-', c['name'], f"{amt:,.0f}"])
            
            data.append(["", "", "Total Spent", f"৳ {total:,.0f}"])
            
            t = Table(data, colWidths=[80, 150, 180, 100])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f1f5f9')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
                ('FONTNAME', (2, -1), (-1, -1), 'Helvetica-Bold'),
            ]))
            elements.append(t)
            
            doc.build(elements)
            execute_query("INSERT INTO audit_logs (user_id, action, entity_type, description) VALUES (%s, %s, %s, %s)",
                         (self.user.get('id'), "CREATE", "report", f"Generated Project {p_id} PDF"), fetch=False)
            messagebox.showinfo("Success", f"PDF saved to {save_path}")
            os.startfile(save_path)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate PDF:\n{e}")

    def generate_investor_pdf(self):
        val = self.inv_var.get()
        if not 'ID:' in val: return messagebox.showerror("Error", "Select an investor first")
        i_id = val.split('ID: ')[1].replace(')', '')
        
        save_path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=f"Investor_Statement_{i_id}.pdf", title="Save Investor Statement")
        if not save_path: return

        try:
            inv = execute_query("SELECT * FROM investors WHERE id=%s", (i_id,))[0]
            inv_recs = execute_query("SELECT amount, date, payment_method FROM investments WHERE investor_id=%s ORDER BY date ASC", (i_id,))
            
            doc = SimpleDocTemplate(save_path, pagesize=letter)
            styles = getSampleStyleSheet()
            elements = []
            
            elements.append(Paragraph(f"CMS Financial Statement", styles['Title']))
            elements.append(Paragraph(f"Investor: {inv['name']} ({inv.get('company') or 'Individual'})", styles['Heading2']))
            elements.append(Spacer(1, 20))
            
            data = [["Date", "Payment Method", "Amount Invested (৳)"]]
            total = 0
            for r in inv_recs:
                amt = float(r['amount'] or 0)
                total += amt
                data.append([format_date(r['date'], default='N/A'), (r['payment_method'] or 'Cash').upper(), f"{amt:,.0f}"])
            
            data.append(["", "Total Investment", f"৳ {total:,.0f}"])
            
            t = Table(data, colWidths=[120, 200, 150])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f1f5f9')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
                ('FONTNAME', (1, -1), (-1, -1), 'Helvetica-Bold'),
            ]))
            elements.append(t)
            
            doc.build(elements)
            execute_query("INSERT INTO audit_logs (user_id, action, entity_type, description) VALUES (%s, %s, %s, %s)",
                         (self.user.get('id'), "CREATE", "report", f"Generated Investor {i_id} Statement"), fetch=False)
            messagebox.showinfo("Success", f"PDF saved to {save_path}")
            os.startfile(save_path)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate PDF:\n{e}")
