"""
Login View for CMS Desktop App.
Modern entry screen with connection status and server setup.
"""

import os
import sys
from tkinter import messagebox

import customtkinter as ctk

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
            ("Local database", "Portable SQLite database for local usage."),
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
            placeholder_text="Username",
            fg_color="#101b35",
            border_color="#233154",
        )
        self.username_entry.insert(0, "admin")
        self.username_entry.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(form, text="Password", font=ctk.CTkFont(size=12, weight="bold"), text_color="#9bb0d5").pack(
            anchor="w", pady=(0, 4)
        )
        pass_frame = ctk.CTkFrame(form, fg_color="transparent")
        pass_frame.pack(fill="x", pady=(0, 20))

        self.password_entry = ctk.CTkEntry(
            pass_frame,
            height=44,
            corner_radius=12,
            placeholder_text="Password",
            show="*",
            fg_color="#101b35",
            border_color="#233154",
        )
        self.password_entry.insert(0, "admin123")
        self.password_entry.pack(side="left", fill="x", expand=True)

        self.show_password = False
        self.eye_btn = ctk.CTkButton(
            pass_frame,
            text="👁",
            width=40,
            height=44,
            corner_radius=12,
            fg_color="#162748",
            hover_color="#223863",
            text_color="#9bb0d5",
            command=self.toggle_password,
        )
        self.eye_btn.pack(side="right", padx=(8, 0))

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
        ok, message = test_connection()
        if ok:
            self.db_status.configure(text="Connected: SQLite Database", text_color="#27d3a2")
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
            try:
                if self.winfo_exists():
                    self.login_btn.configure(state="normal", text="Enter Workspace")
            except Exception:
                # The login frame is destroyed on successful login, so ignore
                # any late widget teardown errors from CustomTkinter.
                pass

    def toggle_password(self):
        self.show_password = not self.show_password
        if self.show_password:
            self.password_entry.configure(show="")
            self.eye_btn.configure(text="🔒")
        else:
            self.password_entry.configure(show="*")
            self.eye_btn.configure(text="👁")
