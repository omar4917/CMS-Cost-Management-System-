"""
AI assistant view for the desktop app.
Keeps chat history on disk and survives tab switches while requests run.
"""

import json
import os
import sys
import threading
import uuid

import customtkinter as ctk

from core import ai_actions, ai_service


WELCOME_MESSAGE = (
    "I can analyze live desktop data, seed full demo records, and execute safe CRUD actions.\n\n"
    "Try prompts like:\n"
    "- Create dummy data for the desktop app\n"
    "- Add a new investor named Tanvir Karim with email tanvir@example.com\n"
    "- Delete project 4\n"
    "- Analyze my cash flow and overdue payments"
)

HISTORY_LOCK = threading.RLock()
MAX_HISTORY = 60


class AIAssistantView(ctk.CTkFrame):
    def __init__(self, parent, user):
        super().__init__(parent, fg_color="transparent")
        self.user = user
        self.chat_history = []
        self._poll_job = None
        self._history_mtime = None
        self._destroyed = False

        if getattr(sys, "frozen", False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        self.history_dir = os.path.join(base_dir, "data")
        self.history_file = os.path.join(self.history_dir, "ai_history.json")
        os.makedirs(self.history_dir, exist_ok=True)

        self.load_history()
        self.build_ui()
        self.refresh_chat()
        self._schedule_history_poll()
        self.bind("<Destroy>", self._on_destroy)

    def load_history(self):
        loaded = self._read_history_from_disk(default=self.chat_history)
        self.chat_history = loaded[-MAX_HISTORY:] if isinstance(loaded, list) else []
        try:
            if os.path.exists(self.history_file):
                self._history_mtime = os.path.getmtime(self.history_file)
        except OSError:
            self._history_mtime = None

    def save_history(self):
        trimmed = self.chat_history[-MAX_HISTORY:]
        temp_file = f"{self.history_file}.tmp"
        try:
            with HISTORY_LOCK:
                with open(temp_file, "w", encoding="utf-8") as handle:
                    json.dump(trimmed, handle, ensure_ascii=False, indent=2)
                os.replace(temp_file, self.history_file)
                self.chat_history = trimmed
                self._history_mtime = os.path.getmtime(self.history_file)
        except Exception as exc:
            print(f"Failed to save AI history: {exc}")
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except OSError:
                pass

    def build_ui(self):
        hero = ctk.CTkFrame(
            self,
            fg_color="#0d1630",
            corner_radius=22,
            border_width=1,
            border_color="#233154",
        )
        hero.pack(fill="x", pady=(0, 14))

        header = ctk.CTkFrame(hero, fg_color="transparent")
        header.pack(fill="x", padx=22, pady=(18, 10))

        title_col = ctk.CTkFrame(header, fg_color="transparent")
        title_col.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(
            title_col,
            text="AI Operations Desk",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="#f8fafc",
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_col,
            text="Ask questions, generate demo data, or issue structured CRUD requests from one place.",
            font=ctk.CTkFont(size=13),
            text_color="#8ea3c7",
        ).pack(anchor="w", pady=(4, 0))

        actions = ctk.CTkFrame(header, fg_color="transparent")
        actions.pack(side="right")
        ctk.CTkButton(
            actions,
            text="Clear",
            width=72,
            height=38,
            corner_radius=10,
            fg_color="#182748",
            hover_color="#223660",
            command=self.clear_chat,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            actions,
            text="Settings",
            width=82,
            height=38,
            corner_radius=10,
            fg_color="#4f8cff",
            hover_color="#3578f6",
            command=self.open_settings,
        ).pack(side="left")

        _, provider = ai_service.get_provider()
        self.provider_label = ctk.CTkLabel(
            hero,
            text=f"Provider: {provider['name']}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#9bb0d5",
        )
        self.provider_label.pack(anchor="w", padx=22, pady=(0, 14))

        quick = ctk.CTkFrame(
            self,
            fg_color="#0d1630",
            corner_radius=18,
            border_width=1,
            border_color="#1f2a45",
        )
        quick.pack(fill="x", pady=(0, 12))

        for label, prompt in [
            ("Seed Demo Data", "Create dummy data for the desktop app"),
            ("Cash Flow", "Analyze my cash flow and overdue payments"),
            ("Project Review", "Analyze all my projects and flag the risky ones"),
            ("Budget Split", "Suggest a budget allocation for a 12-floor residential building in Dhaka"),
        ]:
            ctk.CTkButton(
                quick,
                text=label,
                height=36,
                corner_radius=10,
                fg_color="#152140",
                hover_color="#233154",
                command=lambda query=prompt: self.send_quick(query),
            ).pack(side="left", padx=8, pady=10)

        self.chat_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="#0d1630",
            corner_radius=18,
            border_width=1,
            border_color="#1f2a45",
        )
        self.chat_frame.pack(fill="both", expand=True, pady=(0, 12))

        input_wrap = ctk.CTkFrame(
            self,
            fg_color="#0d1630",
            corner_radius=18,
            border_width=1,
            border_color="#1f2a45",
            height=84,
        )
        input_wrap.pack(fill="x")
        input_wrap.pack_propagate(False)

        self.input_entry = ctk.CTkEntry(
            input_wrap,
            placeholder_text="Describe what you want the desktop app to do...",
            height=46,
            corner_radius=12,
            fg_color="#101b35",
            border_color="#233154",
        )
        self.input_entry.pack(side="left", fill="x", expand=True, padx=(16, 10), pady=18)
        self.input_entry.bind("<Return>", lambda _event: self.send_message())

        self.send_btn = ctk.CTkButton(
            input_wrap,
            text="Send",
            width=96,
            height=46,
            corner_radius=12,
            fg_color="#4f8cff",
            hover_color="#3578f6",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.send_message,
        )
        self.send_btn.pack(side="right", padx=(0, 16), pady=18)

    def refresh_chat(self):
        for widget in self.chat_frame.winfo_children():
            widget.destroy()

        if not self.chat_history:
            self._add_message("assistant", WELCOME_MESSAGE)
        else:
            for message in self.chat_history:
                role = message.get("role")
                content = message.get("content")
                if role and isinstance(content, str):
                    self._add_message(role, content, thinking=bool(message.get("pending")))

        if self.winfo_exists():
            self._update_input_state()

    def _add_message(self, role, content, thinking=False):
        is_user = role == "user"

        row = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=6, anchor="e" if is_user else "w")

        tag = ctk.CTkLabel(
            row,
            text=self.user.get("firstName", "You") if is_user else "AI Desk",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#4f8cff" if is_user else "#9bb0d5",
        )
        tag.pack(anchor="e" if is_user else "w", padx=8, pady=(0, 4))

        bubble = ctk.CTkFrame(
            row,
            fg_color="#152140" if is_user else "#101b35",
            corner_radius=16,
            border_width=1,
            border_color="#233154",
        )
        bubble.pack(anchor="e" if is_user else "w", fill="x")

        box = ctk.CTkTextbox(
            bubble,
            fg_color="transparent",
            text_color="#f8fafc" if not thinking else "#8aa0c8",
            wrap="word",
            font=ctk.CTkFont(size=13),
            height=max(56, (content.count("\n") + len(content) // 90 + 2) * 22),
        )
        box.insert("1.0", content)
        box.configure(state="disabled")
        box.pack(fill="x", padx=12, pady=12)

        self.chat_frame._parent_canvas.yview_moveto(1.0)
        return row

    def send_message(self):
        prompt = self.input_entry.get().strip()
        if not prompt:
            return

        request_id = uuid.uuid4().hex
        self.input_entry.delete(0, "end")
        self.chat_history.append({"role": "user", "content": prompt})
        self.chat_history.append(
            {
                "role": "assistant",
                "content": "Working on that...",
                "pending": True,
                "request_id": request_id,
            }
        )
        self.save_history()
        self.refresh_chat()

        def run_ai():
            response = None
            try:
                local_response = ai_actions.handle_local_command(prompt, user_id=self.user.get("id"))
                if local_response:
                    response = local_response
                else:
                    response = ai_service.chat(self._conversation_window())
                    actions = ai_actions.extract_actions(response)
                    actions_taken = ai_actions.execute_actions(actions, user_id=self.user.get("id"))
                    if actions_taken > 0:
                        response += f"\n\n*(Automatically executed {actions_taken} database actions)*"
            except Exception as exc:
                response = f"Error while processing the request: {exc}"
            finally:
                if not response:
                    response = "The request finished without a response."
                self._finalize_request(request_id, response)
                self._safe_reload()

        threading.Thread(target=run_ai, daemon=True).start()

    def _conversation_window(self):
        latest_history = self._read_history_from_disk(default=self.chat_history)
        trimmed = [message for message in latest_history if not message.get("pending")]
        return trimmed[-12:]

    def _finalize_request(self, request_id, response):
        latest_history = self._read_history_from_disk(default=self.chat_history)
        replaced = False

        for index, message in enumerate(latest_history):
            if message.get("request_id") == request_id and message.get("pending"):
                latest_history[index] = {"role": "assistant", "content": response}
                replaced = True
                break

        if not replaced:
            latest_history.append({"role": "assistant", "content": response})

        self.chat_history = latest_history[-MAX_HISTORY:]
        self.save_history()

    def send_quick(self, prompt):
        self.input_entry.delete(0, "end")
        self.input_entry.insert(0, prompt)
        self.send_message()

    def clear_chat(self):
        self.chat_history = []
        self.save_history()
        self.refresh_chat()

    def open_settings(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("AI Settings")
        dialog.geometry("520x430")
        dialog.configure(fg_color="#0b1327")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="AI Settings", font=ctk.CTkFont(size=24, weight="bold"), text_color="#f8fafc").pack(
            pady=(24, 10)
        )

        form = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=30)

        ctk.CTkLabel(form, text="Provider", font=ctk.CTkFont(size=12, weight="bold"), text_color="#9bb0d5").pack(
            anchor="w", pady=(6, 4)
        )
        provider_var = ctk.StringVar(value=ai_service._config["provider"])
        for key, provider in ai_service.PROVIDERS.items():
            ctk.CTkRadioButton(
                form,
                text=provider["name"],
                variable=provider_var,
                value=key,
                fg_color="#4f8cff",
                hover_color="#3578f6",
                text_color="#d9e4ff",
            ).pack(anchor="w", pady=4)

        ctk.CTkLabel(form, text="API Key", font=ctk.CTkFont(size=12, weight="bold"), text_color="#9bb0d5").pack(
            anchor="w", pady=(16, 4)
        )
        key_entry = ctk.CTkEntry(
            form,
            height=40,
            fg_color="#101b35",
            border_color="#233154",
            corner_radius=10,
            show="*",
        )
        key_entry.insert(0, ai_service._config["api_key"])
        key_entry.pack(fill="x")

        show_var = ctk.BooleanVar(value=False)

        def toggle_show():
            key_entry.configure(show="" if show_var.get() else "*")

        ctk.CTkCheckBox(
            form,
            text="Show API key",
            variable=show_var,
            command=toggle_show,
            text_color="#9bb0d5",
        ).pack(anchor="w", pady=(8, 0))

        ctk.CTkLabel(
            form,
            text="Use Groq, OpenAI, or Gemini credentials. The desktop app stores the last selection in the local .env file on this machine.",
            font=ctk.CTkFont(size=11),
            text_color="#6e84ac",
            wraplength=420,
            justify="left",
        ).pack(anchor="w", pady=(14, 0))

        def save():
            ai_service.save_provider_settings(provider_var.get(), key_entry.get().strip())
            _, provider = ai_service.get_provider()
            self.provider_label.configure(text=f"Provider: {provider['name']}")
            dialog.destroy()

        footer = ctk.CTkFrame(dialog, fg_color="transparent")
        footer.pack(fill="x", padx=30, pady=(10, 24))
        ctk.CTkButton(
            footer,
            text="Cancel",
            fg_color="#182748",
            hover_color="#223660",
            corner_radius=10,
            height=38,
            command=dialog.destroy,
        ).pack(side="left")
        ctk.CTkButton(
            footer,
            text="Save",
            fg_color="#4f8cff",
            hover_color="#3578f6",
            corner_radius=10,
            height=38,
            command=save,
        ).pack(side="right")

    def _update_input_state(self):
        has_pending = any(message.get("pending") for message in self.chat_history)
        if has_pending:
            self.send_btn.configure(state="disabled", text="Running...")
            self.input_entry.configure(state="disabled")
        else:
            self.send_btn.configure(state="normal", text="Send")
            self.input_entry.configure(state="normal")
            self.input_entry.focus()

    def _read_history_from_disk(self, default=None):
        fallback = list(default or [])
        try:
            if not os.path.exists(self.history_file):
                return fallback
            with HISTORY_LOCK:
                with open(self.history_file, "r", encoding="utf-8") as handle:
                    loaded = json.load(handle)
            return loaded if isinstance(loaded, list) else fallback
        except Exception:
            return fallback

    def _reload_from_disk(self):
        self.load_history()
        self.refresh_chat()

    def _safe_reload(self):
        if self._destroyed or not self.winfo_exists():
            return
        try:
            self.after(0, self._reload_from_disk)
        except Exception:
            pass

    def _schedule_history_poll(self):
        if self._destroyed or not self.winfo_exists():
            return
        try:
            if os.path.exists(self.history_file):
                current_mtime = os.path.getmtime(self.history_file)
                if self._history_mtime is None or current_mtime != self._history_mtime:
                    self.load_history()
                    self.refresh_chat()
        except Exception:
            pass
        self._poll_job = self.after(1000, self._schedule_history_poll)

    def _on_destroy(self, _event):
        self._destroyed = True
        if self._poll_job:
            try:
                self.after_cancel(self._poll_job)
            except Exception:
                pass
            self._poll_job = None
