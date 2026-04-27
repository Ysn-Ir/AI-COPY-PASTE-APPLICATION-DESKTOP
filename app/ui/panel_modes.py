"""
ClipboardAI — Modes Panel (black/white/gray theme)
"""

import customtkinter as ctk

BG    = "#0a0a0a"
CARD  = "#141414"
CARD2 = "#1c1c1c"
BDR   = "#2a2a2a"
TEXT1 = "#f0f0f0"
TEXT2 = "#666666"
TEXT3 = "#888888"
SUCCESS = "#22c55e"
DANGER  = "#ef4444"
WARN    = "#f59e0b"


class ModesPanel(ctk.CTkFrame):
    def __init__(self, parent, engine, **kwargs):
        super().__init__(parent, fg_color=BG, **kwargs)
        self._engine = engine
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(self, text="Modes & Prompts",
                     font=ctk.CTkFont(size=22, weight="bold"), text_color=TEXT1
                     ).grid(row=0, column=0, sticky="w", padx=28, pady=(28, 4))
        ctk.CTkLabel(self, text="Each mode has a hotkey, system prompt, and optional web search.",
                     font=ctk.CTkFont(size=12), text_color=TEXT2
                     ).grid(row=1, column=0, sticky="w", padx=28, pady=(0, 14))

        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=2, column=0, sticky="ew", padx=28, pady=(0, 10))
        ctk.CTkButton(bar, text="+ New Mode", height=36,
                      fg_color="#ffffff", hover_color="#dddddd",
                      text_color="#000000", corner_radius=8,
                      font=ctk.CTkFont(size=12, weight="bold"),
                      command=self._add_dialog).pack(side="left")
        self._msg = ctk.CTkLabel(bar, text="", font=ctk.CTkFont(size=11),
                                  text_color=SUCCESS)
        self._msg.pack(side="right", padx=(0, 4))

        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.grid(row=3, column=0, sticky="nsew", padx=28, pady=(0, 28))
        self._scroll.grid_columnconfigure(0, weight=1)

        self._refresh()

    def _refresh(self):
        for w in self._scroll.winfo_children():
            w.destroy()
        cfg   = self._engine.load_config()
        modes = cfg.get("modes", {})
        for i, (name, mcfg) in enumerate(modes.items()):
            self._mode_card(i, name, mcfg)

    def _mode_card(self, row, name, mcfg):
        card = ctk.CTkFrame(self._scroll, fg_color=CARD, corner_radius=10,
                             border_width=1, border_color=BDR)
        card.grid(row=row, column=0, sticky="ew", pady=(0, 8))
        card.grid_columnconfigure(1, weight=1)

        # Icon
        icon = "🌐" if mcfg.get("web_search") else "◈"
        ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=20), width=52,
                     text_color=TEXT3
                     ).grid(row=0, column=0, rowspan=2, padx=(16, 0), pady=14)

        # Info
        top = ctk.CTkFrame(card, fg_color="transparent")
        top.grid(row=0, column=1, sticky="ew", padx=10, pady=(14, 2))

        ctk.CTkLabel(top, text=mcfg.get("label", name),
                     font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT1
                     ).pack(side="left")
        ctk.CTkLabel(top, text=f"  {mcfg.get('hotkey','—')}",
                     font=ctk.CTkFont(size=11), text_color=TEXT3
                     ).pack(side="left")
        if mcfg.get("web_search"):
            ctk.CTkLabel(top, text="  +web", font=ctk.CTkFont(size=10),
                         text_color=WARN).pack(side="left")

        preview = (mcfg.get("prompt", "")[:80] + "…")
        ctk.CTkLabel(card, text=preview, font=ctk.CTkFont(size=11),
                     text_color=TEXT2, anchor="w", wraplength=500
                     ).grid(row=1, column=1, sticky="ew", padx=10, pady=(0, 14))

        # Buttons
        bts = ctk.CTkFrame(card, fg_color="transparent")
        bts.grid(row=0, column=2, rowspan=2, padx=14, pady=14)
        ctk.CTkButton(bts, text="Edit", width=64, height=30,
                      fg_color=CARD2, hover_color=BDR, corner_radius=6,
                      font=ctk.CTkFont(size=11), text_color=TEXT1,
                      command=lambda n=name, m=mcfg: self._edit_dialog(n, m)
                      ).pack(pady=(0, 6))
        ctk.CTkButton(bts, text="Del", width=64, height=30,
                      fg_color="#1a0000", hover_color="#2a0000", corner_radius=6,
                      font=ctk.CTkFont(size=11), text_color=DANGER,
                      command=lambda n=name: self._delete(n)
                      ).pack()

    def _add_dialog(self):
        self._open_dialog(None, {})

    def _edit_dialog(self, name, mcfg):
        self._open_dialog(name, mcfg)

    def _open_dialog(self, existing_name, mcfg):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Edit Mode" if existing_name else "New Mode")
        dlg.geometry("600x620")
        dlg.configure(fg_color="#0d0d0d")
        dlg.grab_set()
        dlg.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(dlg, text="Edit Mode" if existing_name else "New Mode",
                     font=ctk.CTkFont(size=17, weight="bold"), text_color=TEXT1
                     ).grid(row=0, column=0, sticky="w", padx=24, pady=(20, 14))

        fields = {}

        def field(r, lbl, key, ph="", default=""):
            ctk.CTkLabel(dlg, text=lbl, font=ctk.CTkFont(size=11),
                         text_color=TEXT2).grid(row=r*2-1, column=0, sticky="w",
                                                padx=24, pady=(0, 3))
            e = ctk.CTkEntry(dlg, placeholder_text=ph, height=34,
                              font=ctk.CTkFont(size=12),
                              fg_color=CARD, border_color=BDR, text_color=TEXT1)
            e.insert(0, mcfg.get(key, default))
            e.grid(row=r*2, column=0, sticky="ew", padx=24, pady=(0, 4))
            fields[key] = e

        field(1, "Mode ID", "_name", "e.g. summarize", existing_name or "")
        field(2, "Label",   "label", "e.g. Summarize", mcfg.get("label", ""))
        field(3, "Hotkey",  "hotkey", "e.g. ctrl+alt+m", mcfg.get("hotkey", ""))
        field(4, "Description", "description", "", mcfg.get("description", ""))

        ctk.CTkLabel(dlg, text="System Prompt", font=ctk.CTkFont(size=11),
                     text_color=TEXT2).grid(row=9, column=0, sticky="w",
                                            padx=24, pady=(0, 3))
        prompt_box = ctk.CTkTextbox(dlg, height=140,
                                     font=ctk.CTkFont(family="Consolas", size=12),
                                     fg_color=CARD, border_color=BDR, border_width=1,
                                     text_color=TEXT1)
        prompt_box.insert("0.0", mcfg.get("prompt", ""))
        prompt_box.grid(row=10, column=0, sticky="ew", padx=24, pady=(0, 10))

        ws_var = ctk.BooleanVar(value=mcfg.get("web_search", False))
        ws_row = ctk.CTkFrame(dlg, fg_color="transparent")
        ws_row.grid(row=11, column=0, sticky="w", padx=24, pady=(0, 8))
        ctk.CTkLabel(ws_row, text="Enable Web Search",
                     font=ctk.CTkFont(size=12), text_color=TEXT1).pack(side="left", padx=(0, 12))
        ctk.CTkSwitch(ws_row, text="", variable=ws_var,
                       progress_color="#444444", button_color=TEXT1).pack(side="left")

        err = ctk.CTkLabel(dlg, text="", font=ctk.CTkFont(size=11), text_color=DANGER)
        err.grid(row=12, column=0, sticky="w", padx=24)

        def save():
            mode_id = fields["_name"].get().strip().replace(" ", "_")
            hotkey  = fields["hotkey"].get().strip()
            prompt  = prompt_box.get("0.0", "end").strip()
            if not mode_id or not hotkey or not prompt:
                err.configure(text="Mode ID, Hotkey and Prompt are required.")
                return
            cfg   = self._engine.load_config()
            modes = cfg.get("modes", {})
            if existing_name and existing_name != mode_id:
                modes.pop(existing_name, None)
            modes[mode_id] = {
                "hotkey":      hotkey,
                "label":       fields["label"].get().strip() or mode_id,
                "description": fields["description"].get().strip(),
                "prompt":      prompt,
                "web_search":  ws_var.get(),
            }
            cfg["modes"] = modes
            self._engine.save_config(cfg)
            if self._engine.is_running:
                self._engine.restart()
            self._refresh()
            self._msg.configure(text="Saved")
            self.after(3000, lambda: self._msg.configure(text=""))
            dlg.destroy()

        ctk.CTkButton(dlg, text="Save Mode", height=38,
                      fg_color="#ffffff", hover_color="#dddddd",
                      text_color="#000000", corner_radius=8,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=save
                      ).grid(row=13, column=0, sticky="ew", padx=24, pady=(6, 20))

    def _delete(self, name):
        cfg = self._engine.load_config()
        cfg.get("modes", {}).pop(name, None)
        self._engine.save_config(cfg)
        if self._engine.is_running:
            self._engine.restart()
        self._refresh()
        self._msg.configure(text=f"Deleted '{name}'")
        self.after(3000, lambda: self._msg.configure(text=""))
