"""
Audit Trail View for CMS Desktop App.
Displays a log of user activities, creations, updates, and deletions.
"""

import customtkinter as ctk
from core.database import execute_query


class AuditView(ctk.CTkFrame):
    def __init__(self, parent, user):
        super().__init__(parent, fg_color="transparent")
        self.user = user
        self.build_ui()
        self.load_logs()

    def build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(header, text="Audit Trail & Activity Log", font=ctk.CTkFont(size=26, weight="bold"),
                    text_color="white").pack(side="left")

        # Filters
        filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        filter_frame.pack(fill="x", pady=(0, 10))

        self.action_var = ctk.StringVar(value="All Actions")
        ctk.CTkOptionMenu(filter_frame, variable=self.action_var,
                         values=["All Actions", "CREATE", "UPDATE", "DELETE", "LOGIN"],
                         command=lambda _: self.load_logs(),
                         fg_color="#1e293b", button_color="#334155",
                         height=38, width=200).pack(side="left")

        # Table
        self.table_frame = ctk.CTkScrollableFrame(self, fg_color="#111827", corner_radius=12)
        self.table_frame.pack(fill="both", expand=True)

    def load_logs(self):
        for w in self.table_frame.winfo_children():
            w.destroy()

        a_filter = self.action_var.get()

        try:
            query = """
                SELECT a.id, a.action, a.description, a.entity_type, a.created_at, u.username
                FROM audit_logs a
                LEFT JOIN users u ON a.user_id = u.id
                WHERE 1=1
            """
            params = []
            
            if a_filter != "All Actions":
                query += " AND UPPER(a.action) = UPPER(%s)"
                params.append(a_filter)
                
            query += " ORDER BY a.created_at DESC LIMIT 100"
            
            logs = execute_query(query, params)

            hdr = ctk.CTkFrame(self.table_frame, fg_color="#0f172a")
            hdr.pack(fill="x", padx=5, pady=(5, 0))
            for text, w in [("Time", 140), ("User", 100), ("Action", 90), ("Entity", 120), ("Description", 400)]:
                ctk.CTkLabel(hdr, text=text, font=ctk.CTkFont(size=11, weight="bold"),
                            text_color="#64748b", width=w, anchor="w").pack(side="left", padx=4, pady=8)

            if not logs:
                empty = ctk.CTkFrame(self.table_frame, fg_color="transparent")
                empty.pack(pady=40)
                ctk.CTkLabel(empty, text="No activity logs found.", text_color="#64748b").pack()
                return

            color_map = {'create': '#10b981', 'update': '#3b82f6', 'delete': '#ef4444', 'login': '#8b5cf6'}

            for log in logs:
                row = ctk.CTkFrame(self.table_frame, fg_color="transparent")
                row.pack(fill="x", padx=5)
                row.bind("<Enter>", lambda e, r=row: r.configure(fg_color="#1e293b"))
                row.bind("<Leave>", lambda e, r=row: r.configure(fg_color="transparent"))

                date_str = log['created_at'].strftime('%Y-%m-%d %H:%M:%S') if log.get('created_at') else 'N/A'
                ctk.CTkLabel(row, text=date_str, font=ctk.CTkFont(size=11),
                            text_color="#94a3b8", width=140, anchor="w").pack(side="left", padx=4, pady=6)

                username = log.get('username') or 'System'
                ctk.CTkLabel(row, text=username[:15], font=ctk.CTkFont(size=12, weight="bold"),
                            text_color="#e2e8f0", width=100, anchor="w").pack(side="left", padx=4)

                action = str(log.get('action') or '').lower()
                c_color = color_map.get(action, '#cbd5e1')
                ctk.CTkLabel(row, text=action.upper(), font=ctk.CTkFont(size=11, weight="bold"),
                            text_color=c_color, width=90, anchor="w").pack(side="left", padx=4)

                ent = str(log.get('entity_type') or '')
                ctk.CTkLabel(row, text=ent.capitalize(), font=ctk.CTkFont(size=11),
                            text_color="#94a3b8", width=120, anchor="w").pack(side="left", padx=4)

                desc = str(log.get('description') or '')
                ctk.CTkLabel(row, text=desc, font=ctk.CTkFont(size=12),
                            text_color="#cbd5e1", width=400, anchor="w", wraplength=380).pack(side="left", padx=4)

        except Exception as e:
            ctk.CTkLabel(self.table_frame, text=f"Error loading logs: {e}", text_color="#ef4444").pack(pady=20)
