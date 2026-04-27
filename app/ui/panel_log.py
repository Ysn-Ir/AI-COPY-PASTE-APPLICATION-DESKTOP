"""
ClipboardAI — Log Viewer Panel
Shows log.txt contents with auto-refresh and clear button.
"""

import customtkinter as ctk

BG    = "#0a0a0a"
CARD  = "#141414"
CARD2 = "#1c1c1c"
BDR   = "#2a2a2a"
TEXT1 = "#f0f0f0"
TEXT2 = "#666666"
MONO  = "#a0a0a0"
DANGER= "#ef4444"
SUCCESS="#22c55e"


class LogPanel(ctk.CTkFrame):
    def __init__(self, parent, engine, **kwargs):
        super().__init__(parent, fg_color=BG, **kwargs)
        self._engine = engine
        self._auto_refresh = True
        self._build()
        self._schedule_refresh()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Header row
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=28, pady=(28, 4))
        hdr.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(hdr, text="Activity Log",
                     font=ctk.CTkFont(size=22, weight="bold"),
                     text_color=TEXT1).grid(row=0, column=0, sticky="w")

        btn_row = ctk.CTkFrame(hdr, fg_color="transparent")
        btn_row.grid(row=0, column=2, sticky="e")

        self._auto_var = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(btn_row, text="Auto-refresh", variable=self._auto_var,
                      progress_color="#444444", button_color=TEXT1,
                      font=ctk.CTkFont(size=12), text_color=TEXT2,
                      command=self._toggle_auto).pack(side="left", padx=(0, 12))

        ctk.CTkButton(btn_row, text="Refresh", width=80, height=32,
                      fg_color=CARD2, hover_color=BDR, corner_radius=8,
                      font=ctk.CTkFont(size=12), text_color=TEXT1,
                      command=self._refresh).pack(side="left", padx=(0, 8))

        ctk.CTkButton(btn_row, text="Clear", width=70, height=32,
                      fg_color="#2a0000", hover_color="#3a0000", corner_radius=8,
                      font=ctk.CTkFont(size=12), text_color=DANGER,
                      command=self._clear).pack(side="left")

        ctk.CTkLabel(self, text="Real-time view of log.txt — all AI requests and responses",
                     font=ctk.CTkFont(size=12), text_color=TEXT2
                     ).grid(row=1, column=0, sticky="w", padx=28, pady=(0, 12))

        # Log textbox
        self._textbox = ctk.CTkTextbox(
            self,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color=CARD,
            text_color=MONO,
            border_color=BDR,
            border_width=1,
            wrap="word",
            state="disabled",
        )
        self._textbox.grid(row=2, column=0, sticky="nsew", padx=28, pady=(0, 28))
        self._refresh()

    def _refresh(self):
        text = self._engine.get_log_text()
        self._textbox.configure(state="normal")
        self._textbox.delete("0.0", "end")
        if text.strip():
            self._textbox.insert("0.0", text)
            self._textbox.see("end")
        else:
            self._textbox.insert("0.0", "No log entries yet.\n\nUse a hotkey to send clipboard to AI — it will appear here.")
        self._textbox.configure(state="disabled")

    def _clear(self):
        self._engine.clear_log()
        self._refresh()

    def _toggle_auto(self):
        self._auto_refresh = self._auto_var.get()

    def _schedule_refresh(self):
        if self._auto_refresh:
            self._refresh()
        self.after(3000, self._schedule_refresh)
