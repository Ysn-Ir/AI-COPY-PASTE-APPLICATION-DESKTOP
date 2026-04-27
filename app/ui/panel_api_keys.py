"""
ClipboardAI — API Keys Panel (scrollable, black/white/gray theme)
"""

import threading
import customtkinter as ctk

BG    = "#0a0a0a"
CARD  = "#141414"
CARD2 = "#1c1c1c"
BDR   = "#2a2a2a"
TEXT1 = "#f0f0f0"
TEXT2 = "#666666"
SUCCESS = "#22c55e"
DANGER  = "#ef4444"
WARN    = "#f59e0b"


class ApiKeysPanel(ctk.CTkFrame):
    def __init__(self, parent, engine, **kwargs):
        super().__init__(parent, fg_color=BG, **kwargs)
        self._engine = engine
        self._entries: dict = {}
        self._test_labels: dict = {}
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ── Outer scrollable container ──────────────────────────────────────
        scroll = ctk.CTkScrollableFrame(self, fg_color=BG, scrollbar_button_color=CARD2,
                                         scrollbar_button_hover_color=BDR)
        scroll.grid(row=0, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        # ── Header ─────────────────────────────────────────────────────────
        ctk.CTkLabel(scroll, text="API Keys",
                     font=ctk.CTkFont(size=22, weight="bold"), text_color=TEXT1
                     ).grid(row=0, column=0, sticky="w", padx=28, pady=(28, 4))
        ctk.CTkLabel(scroll,
                     text="Keys are stored locally in .env — never uploaded anywhere",
                     font=ctk.CTkFont(size=12), text_color=TEXT2
                     ).grid(row=1, column=0, sticky="w", padx=28, pady=(0, 20))

        keys = self._engine.get_api_keys()

        providers = [
            {"key": "GEMINI_API_KEY",  "label": "Google Gemini",
             "badge": "Free · Recommended", "link": "aistudio.google.com/app/apikey"},
            {"key": "GROQ_API_KEY",    "label": "Groq",
             "badge": "Free · Very Fast",   "link": "console.groq.com/keys"},
            {"key": "OPENAI_API_KEY",  "label": "OpenAI / Compatible",
             "badge": "Paid · Ollama OK",   "link": "platform.openai.com/api-keys"},
        ]

        for i, p in enumerate(providers):
            self._provider_card(scroll, i + 2, p, keys.get(p["key"], ""))

        # ── OpenAI Base URL ────────────────────────────────────────────────
        url_card = self._card(scroll, 5)
        url_card.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(url_card, text="OpenAI Base URL",
                     font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT1
                     ).grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(14, 2))
        ctk.CTkLabel(url_card,
                     text="Leave blank for OpenAI.  Set http://localhost:11434/v1 for Ollama.",
                     font=ctk.CTkFont(size=11), text_color=TEXT2
                     ).grid(row=1, column=0, columnspan=2, sticky="w", padx=20, pady=(0, 6))
        url_e = ctk.CTkEntry(url_card, placeholder_text="https://api.openai.com/v1",
                              height=36, font=ctk.CTkFont(size=13),
                              fg_color=CARD2, border_color=BDR, text_color=TEXT1)
        url_e.insert(0, keys.get("OPENAI_BASE_URL", ""))
        url_e.grid(row=2, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 14))
        self._entries["OPENAI_BASE_URL"] = url_e

        # ── Env path info ─────────────────────────────────────────────────
        env_card = self._card(scroll, 6)
        env_info = self._engine.get_api_keys()  # triggers reload so we know which .env was used
        from pathlib import Path
        import sys
        if getattr(sys, "frozen", False):
            base = Path(sys.executable).parent
        else:
            base = Path(__file__).parent.parent.parent
        env_path = base / ".env"
        ctk.CTkLabel(env_card,
                     text=f"Keys file: {env_path}",
                     font=ctk.CTkFont(family="Consolas", size=11), text_color=TEXT2
                     ).grid(row=0, column=0, sticky="w", padx=20, pady=12)

        # ── Save row ───────────────────────────────────────────────────────
        save_row = ctk.CTkFrame(scroll, fg_color="transparent")
        save_row.grid(row=7, column=0, sticky="e", padx=28, pady=(4, 28))
        self._save_lbl = ctk.CTkLabel(save_row, text="", font=ctk.CTkFont(size=12),
                                       text_color=SUCCESS)
        self._save_lbl.grid(row=0, column=0, padx=(0, 14))
        ctk.CTkButton(save_row, text="Save Keys", width=130, height=38,
                      fg_color="#ffffff", hover_color="#dddddd",
                      text_color="#000000", corner_radius=8,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=self._save).grid(row=0, column=1)

    # ── Helpers ────────────────────────────────────────────────────────────

    def _card(self, parent, row):
        f = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=10,
                         border_width=1, border_color=BDR)
        f.grid(row=row, column=0, sticky="ew", padx=28, pady=(0, 10))
        return f

    def _provider_card(self, parent, row, p, current_value):
        card = self._card(parent, row)
        card.grid_columnconfigure(1, weight=1)

        # Left accent bar
        ctk.CTkFrame(card, fg_color="#333333", width=3, corner_radius=0
                     ).grid(row=0, column=0, rowspan=3, sticky="ns")

        # Header row
        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.grid(row=0, column=1, sticky="ew", padx=(12, 16), pady=(14, 2))
        hdr.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(hdr, text=p["label"],
                     font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT1
                     ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(hdr, text=f"  {p['badge']}",
                     font=ctk.CTkFont(size=10), text_color=TEXT2
                     ).grid(row=0, column=1, sticky="w")
        test_lbl = ctk.CTkLabel(hdr, text="", font=ctk.CTkFont(size=10), text_color=TEXT2)
        test_lbl.grid(row=0, column=2, sticky="e")
        self._test_labels[p["key"]] = test_lbl

        # Link
        ctk.CTkLabel(card, text=f"  Get key: {p['link']}",
                     font=ctk.CTkFont(size=10), text_color=TEXT2
                     ).grid(row=1, column=1, sticky="w", padx=(12, 16), pady=(0, 6))

        # Input row
        inp = ctk.CTkFrame(card, fg_color="transparent")
        inp.grid(row=2, column=1, sticky="ew", padx=(12, 16), pady=(0, 14))
        inp.grid_columnconfigure(0, weight=1)

        entry = ctk.CTkEntry(inp, placeholder_text="Paste API key here",
                              show="•", height=36, font=ctk.CTkFont(size=13),
                              fg_color=CARD2, border_color=BDR, text_color=TEXT1)
        if current_value:
            entry.insert(0, current_value)
        entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self._entries[p["key"]] = entry

        def make_toggle(e):
            def _t():
                e.configure(show="" if e.cget("show") == "•" else "•")
            return _t

        ctk.CTkButton(inp, text="Show", width=52, height=36,
                      fg_color=CARD2, hover_color=BDR, corner_radius=6,
                      font=ctk.CTkFont(size=11), text_color=TEXT1,
                      command=make_toggle(entry)
                      ).grid(row=0, column=1, padx=(0, 6))

        def make_test(key, lbl):
            def _test():
                lbl.configure(text="...", text_color=WARN)
                val = self._entries[key].get().strip()
                threading.Thread(
                    target=self._test_key, args=(key, val, lbl), daemon=True
                ).start()
            return _test

        ctk.CTkButton(inp, text="Test", width=52, height=36,
                      fg_color="#333333", hover_color=BDR, corner_radius=6,
                      font=ctk.CTkFont(size=11), text_color=TEXT1,
                      command=make_test(p["key"], test_lbl)
                      ).grid(row=0, column=2)

    def _test_key(self, key, value, lbl):
        ok, msg = False, "No key"
        try:
            if not value:
                msg = "Empty"
            elif key == "GEMINI_API_KEY":
                from google import genai
                list(genai.Client(api_key=value).models.list())
                ok, msg = True, "Valid"
            elif key == "GROQ_API_KEY":
                import requests
                r = requests.get(
                    "https://api.groq.com/openai/v1/models",
                    headers={"Authorization": f"Bearer {value}"},
                    timeout=8,
                )
                ok  = r.status_code == 200
                msg = "Valid" if ok else f"HTTP {r.status_code}"
            elif key == "OPENAI_API_KEY":
                import requests
                base_entry = self._entries.get("OPENAI_BASE_URL")
                url = (base_entry.get().strip() if base_entry else "") or "https://api.openai.com/v1"
                r = requests.get(
                    f"{url}/models",
                    headers={"Authorization": f"Bearer {value}"},
                    timeout=8,
                )
                ok  = r.status_code == 200
                msg = "Valid" if ok else f"HTTP {r.status_code}"
        except Exception as exc:
            msg = str(exc)[:50]
        color = SUCCESS if ok else DANGER
        self.after(0, lambda: lbl.configure(text=msg, text_color=color))

    def _save(self):
        keys = {k: e.get().strip() for k, e in self._entries.items()}
        self._engine.save_api_keys(keys)
        self._save_lbl.configure(text="Saved")
        self.after(3000, lambda: self._save_lbl.configure(text=""))
