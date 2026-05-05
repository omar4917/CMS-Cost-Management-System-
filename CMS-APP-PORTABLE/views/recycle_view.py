"""
Recycle Bin view for the desktop app.
Shows deleted records captured from delete actions and supports restore/purge.
"""

from __future__ import annotations

from tkinter import messagebox, ttk

import customtkinter as ctk

from core.database import execute_query
from core.recycle_bin import purge_recycle_entries, restore_recycle_entry


def _short(text: str | None, n: int = 80) -> str:
    if not text:
        return ""
    text = str(text).replace("\n", " ").strip()
    return text if len(text) <= n else text[: n - 3] + "..."


class RecycleBinView(ctk.CTkFrame):
    def __init__(self, parent, user):
        super().__init__(parent, fg_color="transparent")
        self.user = user
        self.tables = []
        self.rows_by_id = {}
        self.bulk_select_var = ctk.BooleanVar(value=False)

        self.build_ui()
        self.load_tables()
        self.load_entries()

    def build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(header, text="Recycle Bin", font=ctk.CTkFont(size=26, weight="bold"), text_color="white").pack(
            side="left"
        )
        ctk.CTkButton(
            header,
            text="Refresh",
            fg_color="#1e293b",
            hover_color="#334155",
            corner_radius=8,
            height=36,
            command=self.load_entries,
        ).pack(side="right")
        ctk.CTkButton(
            header,
            text="Purge Selected",
            fg_color="#ef4444",
            hover_color="#dc2626",
            corner_radius=8,
            height=36,
            command=self.purge_selected,
        ).pack(side="right", padx=(0, 10))
        ctk.CTkButton(
            header,
            text="Restore Selected",
            fg_color="#10b981",
            hover_color="#059669",
            corner_radius=8,
            height=36,
            command=self.restore_selected,
        ).pack(side="right", padx=(0, 10))

        filters = ctk.CTkFrame(self, fg_color="transparent")
        filters.pack(fill="x", pady=(0, 10))

        self.table_var = ctk.StringVar(value="All Tables")
        self.table_menu = ctk.CTkOptionMenu(
            filters,
            variable=self.table_var,
            values=["All Tables"],
            command=lambda *_: self.load_entries(),
            fg_color="#1e293b",
            button_color="#334155",
            height=38,
            width=260,
        )
        self.table_menu.pack(side="left")

        self.show_restored_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            filters,
            text="Show restored",
            variable=self.show_restored_var,
            command=self.load_entries,
            fg_color="#4f8cff",
            hover_color="#3578f6",
            text_color="#c8d6f1",
        ).pack(side="left", padx=(14, 0))

        ctk.CTkCheckBox(
            filters,
            text="Bulk select",
            variable=self.bulk_select_var,
            fg_color="#4f8cff",
            hover_color="#3578f6",
            text_color="#c8d6f1",
        ).pack(side="left", padx=(14, 0))

        self.summary = ctk.CTkLabel(filters, text="", font=ctk.CTkFont(size=12), text_color="#94a3b8")
        self.summary.pack(side="right")

        self.table_container = ctk.CTkFrame(self, fg_color="#111827", corner_radius=12)
        self.table_container.pack(fill="both", expand=True)
        self.table_container.grid_columnconfigure(0, weight=1)
        self.table_container.grid_rowconfigure(0, weight=1)

        self._init_table()

    def _init_table(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure(
            "Recycle.Treeview",
            background="#111827",
            fieldbackground="#111827",
            foreground="#e2e8f0",
            rowheight=28,
            borderwidth=0,
            relief="flat",
        )
        style.map(
            "Recycle.Treeview",
            background=[("selected", "#1e293b")],
            foreground=[("selected", "#f8fafc")],
        )
        style.configure(
            "Recycle.Treeview.Heading",
            background="#0f172a",
            foreground="#94a3b8",
            relief="flat",
            font=("Segoe UI", 9, "bold"),
        )

        cols = ["id", "entity_table", "entity_id", "deleted_at", "deleted_by", "reason", "restored_at"]
        self.tree = ttk.Treeview(
            self.table_container,
            columns=cols,
            show="headings",
            style="Recycle.Treeview",
            selectmode="extended",
        )

        headings = [
            ("id", "ID", 70, "e"),
            ("entity_table", "TABLE", 160, "w"),
            ("entity_id", "ENTITY ID", 95, "e"),
            ("deleted_at", "DELETED AT", 160, "w"),
            ("deleted_by", "DELETED BY", 110, "w"),
            ("reason", "REASON", 330, "w"),
            ("restored_at", "RESTORED AT", 160, "w"),
        ]
        for key, label, width, anchor in headings:
            self.tree.heading(key, text=label, anchor=anchor)
            self.tree.column(key, width=width, anchor=anchor, stretch=key in {"reason"})

        self.tree.tag_configure("even", background="#111827")
        self.tree.tag_configure("odd", background="#0b1220")
        self.tree.tag_configure("restored", foreground="#94a3b8")

        v_scroll = ttk.Scrollbar(self.table_container, orient="vertical", command=self.tree.yview)
        h_scroll = ttk.Scrollbar(self.table_container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=(10, 0))
        v_scroll.grid(row=0, column=1, sticky="ns", padx=(0, 10), pady=(10, 0))
        h_scroll.grid(row=1, column=0, sticky="ew", padx=(10, 0), pady=(0, 10))

        self.tree.bind("<Button-1>", self._on_tree_click, add=True)
        self.tree.bind("<Double-1>", lambda _e: self.open_selected())
        self.tree.bind("<Return>", lambda _e: self.open_selected())

        self.overlay = ctk.CTkLabel(
            self.table_container,
            text="",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#475569",
        )

    def _show_overlay(self, text: str):
        self.overlay.configure(text=text)
        self.overlay.place(relx=0.5, rely=0.5, anchor="center")

    def _hide_overlay(self):
        self.overlay.place_forget()

    def load_tables(self):
        try:
            rows = execute_query("SELECT DISTINCT entity_table AS t FROM recycle_bin ORDER BY t") or []
            self.tables = [r.get("t") for r in rows if r.get("t")]
            self.table_menu.configure(values=["All Tables"] + self.tables)
        except Exception:
            self.tables = []
            self.table_menu.configure(values=["All Tables"])

    def load_entries(self):
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        self.rows_by_id = {}
        self._hide_overlay()

        table_filter = self.table_var.get()
        show_restored = bool(self.show_restored_var.get())

        query = (
            "SELECT rb.*, u.username AS deleted_by_user, ur.username AS restored_by_user "
            "FROM recycle_bin rb "
            "LEFT JOIN users u ON rb.deleted_by = u.id "
            "LEFT JOIN users ur ON rb.restored_by = ur.id "
            "WHERE 1=1"
        )
        params = []
        if table_filter and table_filter != "All Tables":
            query += " AND rb.entity_table=%s"
            params.append(table_filter)
        if not show_restored:
            query += " AND rb.restored_at IS NULL"
        query += " ORDER BY rb.deleted_at DESC, rb.id DESC LIMIT 2000"

        try:
            rows = execute_query(query, tuple(params))
        except Exception as exc:
            self._show_overlay(f"Error: {exc}")
            return

        rows = rows or []
        if not rows:
            self.summary.configure(text="0 items")
            self._show_overlay("Recycle Bin is empty")
            return

        for idx, row in enumerate(rows):
            rid = int(row.get("id"))
            self.rows_by_id[rid] = row

            deleted_by = row.get("deleted_by_user") or (str(row.get("deleted_by")) if row.get("deleted_by") else "-")
            restored_at = row.get("restored_at")
            values = [
                rid,
                row.get("entity_table") or "",
                row.get("entity_id") or "",
                str(row.get("deleted_at") or ""),
                deleted_by,
                _short(row.get("reason") or ""),
                str(restored_at or ""),
            ]
            tags = ["even" if idx % 2 == 0 else "odd"]
            if restored_at:
                tags.append("restored")
            self.tree.insert("", "end", iid=str(rid), values=values, tags=tuple(tags))

        self.summary.configure(text=f"{len(rows)} items")

    def open_selected(self):
        if bool(self.bulk_select_var.get()):
            return
        sel = self.tree.selection()
        if not sel:
            return
        try:
            rid = int(sel[0])
        except ValueError:
            return
        row = self.rows_by_id.get(rid)
        if not row:
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Recycle Entry #{rid}")
        dialog.geometry("820x680")
        dialog.configure(fg_color="#0f172a")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        ctk.CTkLabel(dialog, text=f"{row.get('entity_table')} / {row.get('entity_id')}", font=ctk.CTkFont(size=18, weight="bold"), text_color="#f8fafc").pack(anchor="w", padx=22, pady=(22, 6))
        ctk.CTkLabel(dialog, text=str(row.get("deleted_at") or ""), font=ctk.CTkFont(size=12), text_color="#94a3b8").pack(anchor="w", padx=22)

        box = ctk.CTkTextbox(dialog, fg_color="#111827", border_color="#223356", border_width=1, corner_radius=12, wrap="word")
        box.pack(fill="both", expand=True, padx=20, pady=(14, 14))
        box.insert("1.0", str(row.get("payload") or ""))
        box.configure(state="disabled")

        footer = ctk.CTkFrame(dialog, fg_color="transparent")
        footer.pack(fill="x", padx=20, pady=(0, 18))
        ctk.CTkButton(footer, text="Close", fg_color="#1e293b", hover_color="#334155", height=38, command=dialog.destroy).pack(side="left")

    def _on_tree_click(self, event):
        """Optional click-to-multi-select without holding Ctrl (Bulk select mode)."""
        if not bool(self.bulk_select_var.get()):
            return
        try:
            region = self.tree.identify_region(event.x, event.y)
            if region not in {"cell", "tree"}:
                return
            iid = self.tree.identify_row(event.y)
            if not iid:
                return
            if iid in self.tree.selection():
                self.tree.selection_remove(iid)
            else:
                self.tree.selection_add(iid)
            return "break"
        except Exception:
            return

    def restore_selected(self):
        selected = [int(i) for i in self.tree.selection() if str(i).isdigit()]
        if not selected:
            messagebox.showinfo("No Selection", "Select one or more recycle entries first.")
            return
        if not messagebox.askyesno("Restore", f"Restore {len(selected)} selected entries?"):
            return
        restored = 0
        for rid in selected:
            try:
                restore_recycle_entry(rid, restored_by=self.user.get("id"))
                restored += 1
            except Exception as exc:
                messagebox.showerror("Restore Failed", f"Entry #{rid}: {exc}")
                break
        if restored:
            self.load_tables()
            self.load_entries()
            messagebox.showinfo("Restored", f"Restored {restored} entries.")

    def purge_selected(self):
        selected = [int(i) for i in self.tree.selection() if str(i).isdigit()]
        if not selected:
            messagebox.showinfo("No Selection", "Select one or more recycle entries first.")
            return
        if not messagebox.askyesno(
            "Purge Permanently",
            f"Permanently delete {len(selected)} recycle entries?\n\nThis cannot be undone.",
        ):
            return
        try:
            purge_recycle_entries(selected)
            self.load_tables()
            self.load_entries()
            messagebox.showinfo("Purged", f"Purged {len(selected)} recycle entries.")
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
