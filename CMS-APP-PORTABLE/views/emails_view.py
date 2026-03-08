"""
Email System View for CMS Desktop App. 
Supports Custom Templates, Dynamic Variables ({name}, {amount}), and Bulk Sending.
"""

import customtkinter as ctk
from tkinter import messagebox
from core.database import execute_query
import smtplib
from email.message import EmailMessage
import os
import threading

class EmailsView(ctk.CTkFrame):
    def __init__(self, parent, user):
        super().__init__(parent, fg_color="transparent")
        self.user = user
        self.investors = []
        self.templates = []
        
        self.build_ui()
        self.load_data()

    def build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(header, text="Email System & Automations", font=ctk.CTkFont(size=26, weight="bold"),
                    text_color="white").pack(side="left")

        # Tabs
        self.tabview = ctk.CTkTabview(self, fg_color="#111827", segmented_button_fg_color="#1e293b",
                                     segmented_button_selected_color="#3b82f6",
                                     segmented_button_selected_hover_color="#2563eb",
                                     text_color="#94a3b8")
        self.tabview.pack(fill="both", expand=True, pady=10)

        self.tab_compose = self.tabview.add("Compose & Send")
        self.tab_templates = self.tabview.add("Custom Templates")
        self.tab_logs = self.tabview.add("Delivery Logs")
        
        self.build_compose_tab()
        self.build_templates_tab()
        self.build_logs_tab()
        
        self.tabview.configure(command=self.on_tab_change)

    def on_tab_change(self):
        sel = self.tabview.get()
        if sel == "Delivery Logs":
            self.load_logs()
        elif sel == "Custom Templates":
            self.load_templates_list()
        elif sel == "Compose & Send":
            self.refresh_compose_dropdowns()

    def load_data(self):
        try:
            # We want all investors with emails
            query = """
                SELECT i.id, i.name, i.email, t.name as type_name
                FROM investors i
                LEFT JOIN investor_types t ON i.type_id = t.id
                WHERE i.email IS NOT NULL AND i.email != ''
            """
            self.investors = execute_query(query)
            self.templates = execute_query("SELECT * FROM email_templates ORDER BY name ASC")
            
            self.refresh_compose_dropdowns()
            self.load_templates_list()
            self.load_logs()
        except Exception as e:
            print(f"Error loading email data: {e}")

    # ================= COMPOSE & SEND TAB =================
    def build_compose_tab(self):
        main = ctk.CTkFrame(self.tab_compose, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=20, pady=10)

        row1 = ctk.CTkFrame(main, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 15))

        # Recipients (Bulk Select)
        left = ctk.CTkFrame(row1, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(left, text="Recipients (Select Multiple)", font=ctk.CTkFont(weight="bold"), text_color="#94a3b8").pack(anchor="w")
        
        self.recipients_frame = ctk.CTkScrollableFrame(left, fg_color="#1e293b", height=120, corner_radius=8)
        self.recipients_frame.pack(fill="both", expand=True, pady=(5, 0))
        
        # Templates
        right = ctk.CTkFrame(row1, fg_color="transparent", width=300)
        right.pack(side="right", fill="y", padx=(20, 0))
        ctk.CTkLabel(right, text="Load Custom Template", font=ctk.CTkFont(weight="bold"), text_color="#94a3b8").pack(anchor="w")
        self.tm_var = ctk.StringVar(value="-- Select Template --")
        self.tm_dropdown = ctk.CTkOptionMenu(right, variable=self.tm_var, values=[], fg_color="#1e293b", 
                                            command=self.apply_template)
        self.tm_dropdown.pack(fill="x", pady=(5, 0))
        
        ctk.CTkLabel(right, text="Dynamic Variables:\n{name}, {email}, {type}\n{project}, {amount}, {date}", 
                    justify="left", font=ctk.CTkFont(size=11), text_color="#64748b").pack(anchor="w", pady=(10, 0))

        # Subject & Body
        ctk.CTkLabel(main, text="Subject", font=ctk.CTkFont(weight="bold"), text_color="#94a3b8").pack(anchor="w", pady=(10, 5))
        self.comp_sub = ctk.CTkEntry(main, fg_color="#1e293b", height=38, corner_radius=8)
        self.comp_sub.pack(fill="x")

        ctk.CTkLabel(main, text="Message Body", font=ctk.CTkFont(weight="bold"), text_color="#94a3b8").pack(anchor="w", pady=(15, 5))
        self.comp_body = ctk.CTkTextbox(main, fg_color="#1e293b", height=200, corner_radius=8)
        self.comp_body.pack(fill="x")

        # Send Button
        self.btn_send = ctk.CTkButton(main, text="🚀 Send to Selected Recipients", height=45, fg_color="#10b981", hover_color="#059669", 
                                     font=ctk.CTkFont(size=14, weight="bold"), command=self.send_bulk_emails)
        self.btn_send.pack(pady=20)
        
        self.recipient_vars = {}

    def refresh_compose_dropdowns(self):
        # Refresh Recipients Checkboxes
        for widget in self.recipients_frame.winfo_children():
            widget.destroy()
            
        self.recipient_vars.clear()
        
        # "Select All" toggle
        select_all_var = ctk.BooleanVar(value=False)
        def toggle_all():
            state = select_all_var.get()
            for v in self.recipient_vars.values():
                v.set(state)
                
        ctk.CTkCheckBox(self.recipients_frame, text="Select All / Select None", variable=select_all_var, 
                       command=toggle_all, text_color="#3b82f6", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(5, 10), padx=5)

        for inv in self.investors:
            var = ctk.BooleanVar(value=False)
            self.recipient_vars[inv['id']] = var
            label = f"{inv['name']} ({inv['email']}) - {inv['type_name'] or 'General'}"
            ctk.CTkCheckBox(self.recipients_frame, text=label, variable=var).pack(anchor="w", pady=3, padx=10)

        # Refresh Templates Dropdown
        tm_opts = ["-- Select Template --"] + [t['name'] for t in self.templates]
        self.tm_dropdown.configure(values=tm_opts)

    def apply_template(self, template_name):
        if template_name == "-- Select Template --":
            return
            
        t = next((x for x in self.templates if x['name'] == template_name), None)
        if t:
            self.comp_sub.delete(0, 'end')
            self.comp_sub.insert(0, t['subject'])
            self.comp_body.delete("1.0", 'end')
            self.comp_body.insert("1.0", t['body'])

    def send_bulk_emails(self):
        selected_ids = [k for k, v in self.recipient_vars.items() if v.get()]
        if not selected_ids:
            return messagebox.showerror("Error", "Please select at least one recipient.")
            
        base_subject = self.comp_sub.get().strip()
        base_body = self.comp_body.get("1.0", "end-1c").strip()
        
        if not base_subject or not base_body:
            return messagebox.showerror("Error", "Subject and Body cannot be empty.")

        admin_email = os.getenv('GMAIL_USER')
        admin_pass = os.getenv('GMAIL_APP_PASS')
        if not admin_email or not admin_pass:
            return messagebox.showerror("Error", "Gmail SMTP credentials (GMAIL_USER, GMAIL_APP_PASS) are not configured in the .env file.")

        selected_investors = [i for i in self.investors if i['id'] in selected_ids]
        
        if not messagebox.askyesno("Confirm Send", f"Are you sure you want to send this email to {len(selected_investors)} recipients?"):
            return

        self.btn_send.configure(state="disabled", text="Sending...")
        
        def _bg_process():
            success = 0
            failed = 0
            
            try:
                # Use a single SMTP connection for all emails
                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                    smtp.login(admin_email, admin_pass)
                    
                    for inv in selected_investors:
                        try:
                            # Replace dynamic variables
                            subj = base_subject.replace('{name}', inv['name']).replace('{email}', inv['email']).replace('{type}', inv['type_name'] or 'Investor')
                            body = base_body.replace('{name}', inv['name']).replace('{email}', inv['email']).replace('{type}', inv['type_name'] or 'Investor')
                            
                            # Note: {project}, {amount}, {date} might be left unresolved if not applicable, could replace with empty string
                            body = body.replace('{project}', '[Project Name]').replace('{amount}', '[Amount]').replace('{date}', '[Date]')
                            
                            msg = EmailMessage()
                            msg.set_content(body)
                            msg['Subject'] = subj
                            msg['From'] = admin_email
                            msg['To'] = inv['email']
                            
                            smtp.send_message(msg)
                            
                            # Log success
                            execute_query("INSERT INTO email_logs (investor_id, to_email, subject, body, status) VALUES (%s, %s, %s, %s, 'sent')", 
                                         (inv['id'], inv['email'], subj, body), fetch=False)
                            success += 1
                        except Exception as e:
                            # Log failure
                            execute_query("INSERT INTO email_logs (investor_id, to_email, subject, body, status, error) VALUES (%s, %s, %s, %s, 'failed', %s)", 
                                         (inv['id'], inv['email'], base_subject, base_body, str(e)), fetch=False)
                            failed += 1
                            
                self.after(0, lambda: messagebox.showinfo("Complete", f"Emails Processed!\nSuccess: {success}\nFailed: {failed}"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("SMTP Error", f"Failed to connect to mail server:\n{e}"))
                
            self.after(0, lambda: self.btn_send.configure(state="normal", text="🚀 Send to Selected Recipients"))

        threading.Thread(target=_bg_process, daemon=True).start()


    # ================= TEMPLATES TAB =================
    def build_templates_tab(self):
        ctrl = ctk.CTkFrame(self.tab_templates, fg_color="transparent")
        ctrl.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(ctrl, text="+ Create New Template", fg_color="#3b82f6", hover_color="#2563eb",
                     command=lambda: self.open_template_dialog()).pack(side="right")
                     
        self.tm_list_frame = ctk.CTkScrollableFrame(self.tab_templates, fg_color="transparent")
        self.tm_list_frame.pack(fill="both", expand=True, padx=10)

    def load_templates_list(self):
        for w in self.tm_list_frame.winfo_children():
            w.destroy()
            
        try:
            self.templates = execute_query("SELECT * FROM email_templates ORDER BY name ASC")
            
            for t in self.templates:
                card = ctk.CTkFrame(self.tm_list_frame, fg_color="#1e293b", corner_radius=8)
                card.pack(fill="x", pady=5)
                
                info = ctk.CTkFrame(card, fg_color="transparent")
                info.pack(side="left", padx=15, pady=15, fill="both", expand=True)
                
                tag = " (System Default)" if t.get('is_system') else ""
                ctk.CTkLabel(info, text=f"{t['name']}{tag}", font=ctk.CTkFont(size=14, weight="bold"), text_color="white", anchor="w").pack(fill="x")
                ctk.CTkLabel(info, text=f"Subject: {t['subject']}", font=ctk.CTkFont(size=12), text_color="#cbd5e1", anchor="w").pack(fill="x", pady=(5, 0))
                
                acts = ctk.CTkFrame(card, fg_color="transparent")
                acts.pack(side="right", padx=15)
                
                ctk.CTkButton(acts, text="Edit", width=60, fg_color="#334155", hover_color="#475569", 
                             command=lambda x=t: self.open_template_dialog(x)).pack(side="left", padx=5)
                             
                if not t.get('is_system'):
                    ctk.CTkButton(acts, text="Delete", width=60, fg_color="#ef4444", hover_color="#dc2626", 
                                 command=lambda x=t: self.delete_template(x)).pack(side="left")

        except Exception as e:
            ctk.CTkLabel(self.tm_list_frame, text=f"Error loading templates: {e}").pack()

    def open_template_dialog(self, t=None):
        d = ctk.CTkToplevel(self)
        d.title("Edit Custom Template" if t else "Create Template")
        d.geometry("600x550")
        d.configure(fg_color="#0f172a")
        d.transient(self.winfo_toplevel())
        d.grab_set()

        ctk.CTkLabel(d, text="Email Template", font=ctk.CTkFont(size=20, weight="bold"), text_color="white").pack(pady=20)
        form = ctk.CTkFrame(d, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=30)
        
        # Name
        ctk.CTkLabel(form, text="Template Name *", text_color="#94a3b8").pack(anchor="w")
        n_ent = ctk.CTkEntry(form, fg_color="#1e293b", width=540)
        n_ent.pack(pady=(0, 10))
        
        # Subject
        ctk.CTkLabel(form, text="Subject *", text_color="#94a3b8").pack(anchor="w")
        s_ent = ctk.CTkEntry(form, fg_color="#1e293b", width=540)
        s_ent.pack(pady=(0, 10))
        
        # Body
        ctk.CTkLabel(form, text="Body * (Use {name}, {type}, {email})", text_color="#94a3b8").pack(anchor="w")
        b_txt = ctk.CTkTextbox(form, fg_color="#1e293b", width=540, height=200)
        b_txt.pack(pady=(0, 15))
        
        if t:
            n_ent.insert(0, t['name'])
            s_ent.insert(0, t['subject'])
            b_txt.insert("1.0", t['body'])
            
            if t.get('is_system'):
                n_ent.configure(state="disabled")

        def save():
            nm = n_ent.get().strip()
            sb = s_ent.get().strip()
            bd = b_txt.get("1.0", "end-1c").strip()
            
            if not nm or not sb or not bd:
                return messagebox.showerror("Error", "All fields required")
                
            try:
                if t:
                    execute_query("UPDATE email_templates SET name=%s, subject=%s, body=%s WHERE id=%s", (nm, sb, bd, t['id']), fetch=False)
                else:
                    execute_query("INSERT INTO email_templates (name, subject, body) VALUES (%s, %s, %s)", (nm, sb, bd), fetch=False)
                d.destroy()
                self.load_templates_list()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ctk.CTkButton(form, text="Save Template", command=save, fg_color="#3b82f6", width=540, height=40).pack()

    def delete_template(self, t):
        if messagebox.askyesno("Confirm Delete", f"Delete template '{t['name']}'?"):
            execute_query("DELETE FROM email_templates WHERE id=%s", (t['id'],), fetch=False)
            self.load_templates_list()


    # ================= LOGS TAB =================
    def build_logs_tab(self):
        self.table = ctk.CTkScrollableFrame(self.tab_logs, fg_color="transparent")
        self.table.pack(fill="both", expand=True, padx=10, pady=10)

    def load_logs(self):
        for w in self.table.winfo_children():
            w.destroy()
            
        try:
            logs = execute_query("SELECT * FROM email_logs ORDER BY sent_at DESC LIMIT 100")
            
            hdr = ctk.CTkFrame(self.table, fg_color="#0f172a")
            hdr.pack(fill="x", padx=5, pady=5)
            for text, w in [("Date", 130), ("To", 200), ("Subject", 300), ("Status", 80), ("Error", 150)]:
                ctk.CTkLabel(hdr, text=text, font=ctk.CTkFont(size=11, weight="bold"), text_color="#64748b", width=w, anchor="w").pack(side="left", padx=4)

            if not logs:
                ctk.CTkLabel(self.table, text="No emails sent yet.", text_color="#64748b").pack(pady=30)
                return

            for log in logs:
                row = ctk.CTkFrame(self.table, fg_color="transparent")
                row.pack(fill="x", padx=5)
                row.bind("<Enter>", lambda e, r=row: r.configure(fg_color="#1e293b"))
                row.bind("<Leave>", lambda e, r=row: r.configure(fg_color="transparent"))

                date_str = log['sent_at'].strftime('%Y-%m-%d %H:%M') if log['sent_at'] else 'Unknown'
                ctk.CTkLabel(row, text=date_str, font=ctk.CTkFont(size=11), text_color="#94a3b8", width=130, anchor="w").pack(side="left", padx=4, pady=6)
                ctk.CTkLabel(row, text=log['to_email'][:30], font=ctk.CTkFont(size=11), text_color="#e2e8f0", width=200, anchor="w").pack(side="left", padx=4)
                ctk.CTkLabel(row, text=log['subject'][:45], font=ctk.CTkFont(size=11), text_color="#94a3b8", width=300, anchor="w").pack(side="left", padx=4)
                
                status = log['status']
                s_color = "#10b981" if status == 'sent' else "#ef4444"
                ctk.CTkLabel(row, text=status.upper(), font=ctk.CTkFont(size=10, weight="bold"), text_color=s_color, width=80, anchor="w").pack(side="left", padx=4)
                
                err_text = ""
                if log.get('error'):
                    err_text = str(log['error'])[:20] + "..." if len(str(log['error'])) > 20 else str(log['error'])
                ctk.CTkLabel(row, text=err_text, font=ctk.CTkFont(size=10), text_color="#ef4444", width=150, anchor="w").pack(side="left", padx=4)

        except Exception as e:
            ctk.CTkLabel(self.table, text=f"Error loading logs: {e}", text_color="#ef4444").pack(pady=20)
