"""
ClipboardAI — Settings Panel (with Ollama support + model discovery)
"""

import threading
import customtkinter as ctk

BG      = "#0a0a0a"
CARD    = "#141414"
CARD2   = "#1c1c1c"
BDR     = "#2a2a2a"
TEXT1   = "#f0f0f0"
TEXT2   = "#666666"
SUCCESS = "#22c55e"
DANGER  = "#ef4444"
WARN    = "#f59e0b"

MODEL_SUGGESTIONS = {
    "gemini": ["gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-1.5-pro", "gemini-1.5-flash"],
    "groq":   ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768", "llama3-8b-8192"],
    "openai": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
    "ollama": [],
}


class SettingsPanel(ctk.CTkFrame):
    def __init__(self, parent, engine, **kwargs):
        super().__init__(parent, fg_color=BG, **kwargs)
        self._engine = engine
        self._model_dd = None
        self._ollama_frame = None
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Outer scrollable container
        self._scroll = ctk.CTkScrollableFrame(self, fg_color=BG,
                                         scrollbar_button_color=CARD2,
                                         scrollbar_button_hover_color=BDR)
        self._scroll.grid(row=0, column=0, sticky="nsew")
        self._scroll.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self._scroll, text="Settings",
                     font=ctk.CTkFont(size=22, weight="bold"), text_color=TEXT1
                     ).grid(row=0, column=0, sticky="w", padx=28, pady=(28, 4))
        ctk.CTkLabel(self._scroll, text="Backend, model, hotkeys, and behavior — reloaded on every hotkey press",
                     font=ctk.CTkFont(size=12), text_color=TEXT2
                     ).grid(row=1, column=0, sticky="w", padx=28, pady=(0, 20))

        cfg = self._engine.load_config()
        cur_backend = cfg.get("backend", "groq")

        # ── AI Backend ─────────────────────────────────────────────────────
        self._section(2, "AI Backend")

        ai_card = self._card(3)
        ai_card.grid_columnconfigure(1, weight=1)

        self._label(ai_card, 0, "Backend")
        self._backend_var = ctk.StringVar(value=cur_backend)
        backend_dd = ctk.CTkComboBox(
            ai_card, values=["groq", "gemini", "openai", "ollama"],
            variable=self._backend_var, height=36,
            font=ctk.CTkFont(size=13), fg_color=CARD2, border_color=BDR,
            button_color="#333333", dropdown_fg_color=CARD,
            text_color=TEXT1, dropdown_text_color=TEXT1,
            command=self._on_backend_change,
        )
        backend_dd.grid(row=0, column=1, sticky="ew", padx=(0, 20), pady=(16, 8))

        self._label(ai_card, 1, "Model")
        self._model_var = ctk.StringVar(value=cfg.get("model", ""))
        self._model_dd = ctk.CTkComboBox(
            ai_card, values=MODEL_SUGGESTIONS.get(cur_backend, []),
            variable=self._model_var, height=36,
            font=ctk.CTkFont(size=13), fg_color=CARD2, border_color=BDR,
            button_color="#333333", dropdown_fg_color=CARD,
            text_color=TEXT1, dropdown_text_color=TEXT1,
        )
        self._model_dd.grid(row=1, column=1, sticky="ew", padx=(0, 20), pady=(0, 8))

        # ── Ollama section (shown only when backend=ollama) ────────────────
        self._ollama_frame = ctk.CTkFrame(ai_card, fg_color="transparent")
        self._ollama_frame.grid_columnconfigure(1, weight=1)

        self._label(self._ollama_frame, 0, "Ollama URL")
        self._ollama_url_var = ctk.StringVar(value=cfg.get("ollama_url", "http://localhost:11434"))
        ctk.CTkEntry(self._ollama_frame, textvariable=self._ollama_url_var, height=36,
                     font=ctk.CTkFont(size=13), fg_color=CARD2, border_color=BDR,
                     text_color=TEXT1,
                     ).grid(row=0, column=1, sticky="ew", padx=(0, 20), pady=(0, 8))

        disc_row = ctk.CTkFrame(self._ollama_frame, fg_color="transparent")
        disc_row.grid(row=1, column=1, sticky="w", padx=(0, 20), pady=(0, 16))
        self._disc_btn = ctk.CTkButton(
            disc_row, text="Discover Models", width=150, height=34,
            fg_color=CARD2, hover_color=BDR, corner_radius=8,
            font=ctk.CTkFont(size=12), text_color=TEXT1,
            command=self._discover_ollama,
        )
        self._disc_btn.pack(side="left", padx=(0, 10))
        self._disc_status = ctk.CTkLabel(disc_row, text="", font=ctk.CTkFont(size=11),
                                          text_color=TEXT2)
        self._disc_status.pack(side="left")

        # Show/hide ollama section based on current backend
        if cur_backend == "ollama":
            self._ollama_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=20)
        else:
            self._ollama_frame.grid_remove()

        # ── Hotkeys ────────────────────────────────────────────────────────
        self._section(4, "Hotkeys")
        hk_card = self._card(5)
        hk_card.grid_columnconfigure(1, weight=1)

        self._label(hk_card, 0, "Undo Hotkey")
        self._undo_var = ctk.StringVar(value=cfg.get("hotkey_undo", "ctrl+alt+z"))
        ctk.CTkEntry(hk_card, textvariable=self._undo_var, height=36,
                     font=ctk.CTkFont(size=13), fg_color=CARD2, border_color=BDR,
                     text_color=TEXT1,
                     ).grid(row=0, column=1, sticky="ew", padx=(0, 20), pady=(16, 16))

        # ── Behavior ───────────────────────────────────────────────────────
        self._section(6, "Behavior")
        beh_card = self._card(7)
        beh_card.grid_columnconfigure(1, weight=1)

        self._label(beh_card, 0, "Timeout (seconds)")
        self._timeout_var = ctk.IntVar(value=cfg.get("timeout_seconds", 30))
        t_frame = ctk.CTkFrame(beh_card, fg_color="transparent")
        t_frame.grid(row=0, column=1, sticky="ew", padx=(0, 20), pady=(16, 8))
        t_frame.grid_columnconfigure(0, weight=1)
        self._t_lbl = ctk.CTkLabel(t_frame, text=f"{self._timeout_var.get()}s",
                                    font=ctk.CTkFont(size=13, weight="bold"),
                                    text_color=TEXT1, width=40)
        self._t_lbl.grid(row=0, column=1, padx=(8, 0))
        ctk.CTkSlider(t_frame, from_=5, to=120, number_of_steps=115,
                      variable=self._timeout_var,
                      progress_color="#444444", button_color=TEXT1,
                      command=lambda v: self._t_lbl.configure(text=f"{int(v)}s"),
                      ).grid(row=0, column=0, sticky="ew")

        self._label(beh_card, 1, "Start Minimized to Tray")
        self._min_var = ctk.BooleanVar(value=cfg.get("start_minimized", False))
        ctk.CTkSwitch(beh_card, text="", variable=self._min_var,
                       progress_color="#444444", button_color=TEXT1,
                       ).grid(row=1, column=1, sticky="w", padx=(0, 20), pady=(0, 16))

        # ── Save ───────────────────────────────────────────────────────────
        save_row = ctk.CTkFrame(self._scroll, fg_color="transparent")
        save_row.grid(row=8, column=0, sticky="e", padx=28, pady=(8, 28))
        self._save_lbl = ctk.CTkLabel(save_row, text="", font=ctk.CTkFont(size=12),
                                       text_color=SUCCESS)
        self._save_lbl.grid(row=0, column=0, padx=(0, 14))
        ctk.CTkButton(save_row, text="Save Settings", width=140, height=38,
                      fg_color="#ffffff", hover_color="#dddddd", corner_radius=8,
                      font=ctk.CTkFont(size=13, weight="bold"), text_color="#000000",
                      command=self._save).grid(row=0, column=1)

    # ── Helpers ────────────────────────────────────────────────────────────

    def _section(self, row, title):
        ctk.CTkLabel(self._scroll, text=title,
                     font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT2
                     ).grid(row=row, column=0, sticky="w", padx=28, pady=(8, 4))

    def _card(self, row):
        f = ctk.CTkFrame(self._scroll, fg_color=CARD, corner_radius=10,
                         border_width=1, border_color=BDR)
        f.grid(row=row, column=0, sticky="ew", padx=28, pady=(0, 12))
        return f

    def _label(self, card, row, text):
        ctk.CTkLabel(card, text=text, font=ctk.CTkFont(size=12),
                     text_color=TEXT2, width=180, anchor="w"
                     ).grid(row=row, column=0, sticky="w", padx=20)

    def _on_backend_change(self, value):
        suggestions = MODEL_SUGGESTIONS.get(value, [])
        self._model_dd.configure(values=suggestions)
        if suggestions:
            self._model_var.set(suggestions[0])
        if value == "ollama":
            self._ollama_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=20)
            # Auto-discover
            threading.Thread(target=self._do_discover, daemon=True).start()
        else:
            self._ollama_frame.grid_remove()

    def _discover_ollama(self):
        self._disc_btn.configure(state="disabled")
        self._disc_status.configure(text="Discovering...", text_color=WARN)
        threading.Thread(target=self._do_discover, daemon=True).start()

    def _do_discover(self):
        url = self._ollama_url_var.get().strip()
        models = self._engine.get_ollama_models(url)
        def update():
            self._disc_btn.configure(state="normal")
            if models:
                self._model_dd.configure(values=models)
                self._model_var.set(models[0])
                self._disc_status.configure(
                    text=f"Found {len(models)} model(s)", text_color=SUCCESS)
            else:
                self._disc_status.configure(
                    text="No models found — is Ollama running?", text_color=DANGER)
        self.after(0, update)

    def _save(self):
        cfg = self._engine.load_config()
        cfg["backend"]         = self._backend_var.get()
        cfg["model"]           = self._model_var.get()
        cfg["hotkey_undo"]     = self._undo_var.get()
        cfg["timeout_seconds"] = int(self._timeout_var.get())
        cfg["start_minimized"] = self._min_var.get()
        cfg["ollama_url"]      = self._ollama_url_var.get().strip()
        self._engine.save_config(cfg)
        if self._engine.is_running:
            self._engine.restart()
        self._save_lbl.configure(text="Saved")
        self.after(3000, lambda: self._save_lbl.configure(text=""))
