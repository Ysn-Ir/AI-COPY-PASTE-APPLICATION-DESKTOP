"""
ClipboardAI — Dashboard Panel (black/white/gray theme)
"""

import customtkinter as ctk
from datetime import datetime

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


class DashboardPanel(ctk.CTkFrame):
    def __init__(self, parent, engine, **kwargs):
        super().__init__(parent, fg_color=BG, **kwargs)
        self._engine = engine
        self._engine.add_callback(self._on_engine_event)
        self._query_count = 0
        self._feed_rows = []
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)

        # Header
        ctk.CTkLabel(self, text="Dashboard",
                     font=ctk.CTkFont(size=22, weight="bold"), text_color=TEXT1
                     ).grid(row=0, column=0, sticky="w", padx=28, pady=(28, 4))
        ctk.CTkLabel(self, text="Monitor and control your AI clipboard assistant",
                     font=ctk.CTkFont(size=12), text_color=TEXT2
                     ).grid(row=1, column=0, sticky="w", padx=28, pady=(0, 20))

        # Status card
        sc = ctk.CTkFrame(self, fg_color=CARD, corner_radius=10,
                          border_width=1, border_color=BDR)
        sc.grid(row=2, column=0, sticky="ew", padx=28, pady=(0, 14))
        sc.grid_columnconfigure(1, weight=1)

        self._dot = ctk.CTkLabel(sc, text="●", font=ctk.CTkFont(size=24),
                                  text_color=DANGER)
        self._dot.grid(row=0, column=0, padx=(20, 14), pady=20)

        info = ctk.CTkFrame(sc, fg_color="transparent")
        info.grid(row=0, column=1, sticky="w", pady=20)
        self._status_lbl = ctk.CTkLabel(info, text="Stopped",
                                         font=ctk.CTkFont(size=15, weight="bold"),
                                         text_color=TEXT1)
        self._status_lbl.grid(row=0, column=0, sticky="w")
        self._backend_lbl = ctk.CTkLabel(info, text="Loading...",
                                          font=ctk.CTkFont(size=11), text_color=TEXT2)
        self._backend_lbl.grid(row=1, column=0, sticky="w")

        self._toggle_btn = ctk.CTkButton(
            sc, text="Start", width=110, height=36,
            fg_color="#ffffff", hover_color="#dddddd",
            text_color="#000000", corner_radius=8,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._toggle,
        )
        self._toggle_btn.grid(row=0, column=2, padx=20, pady=20)

        # Stats row
        stats = ctk.CTkFrame(self, fg_color="transparent")
        stats.grid(row=3, column=0, sticky="ew", padx=28, pady=(0, 14))
        for i in range(3):
            stats.grid_columnconfigure(i, weight=1)

        self._stat_count = self._stat_card(stats, 0, "0",  "Queries")
        self._stat_mode  = self._stat_card(stats, 1, "—",  "Last Mode")
        self._stat_time  = self._stat_card(stats, 2, "—",  "Last Time")

        # Activity feed
        ctk.CTkLabel(self, text="Activity",
                     font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT2
                     ).grid(row=4, column=0, sticky="w", padx=28, pady=(0, 6))

        self._feed = ctk.CTkScrollableFrame(self, fg_color=CARD, corner_radius=10,
                                             border_width=1, border_color=BDR,
                                             height=180)
        self._feed.grid(row=5, column=0, sticky="nsew", padx=28, pady=(0, 28))
        self._feed.grid_columnconfigure(0, weight=1)

        self._refresh_status()

    def _stat_card(self, parent, col, value, label):
        pad = (8 if col > 0 else 0, 0)
        card = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=10,
                             border_width=1, border_color=BDR)
        card.grid(row=0, column=col, sticky="ew", padx=pad)
        v = ctk.CTkLabel(card, text=value,
                         font=ctk.CTkFont(size=22, weight="bold"), text_color=TEXT1)
        v.grid(row=0, column=0, padx=20, pady=(14, 2))
        ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=10),
                     text_color=TEXT2).grid(row=1, column=0, padx=20, pady=(0, 12))
        return v

    def _toggle(self):
        if self._engine.is_running:
            self._engine.stop()
        else:
            self._engine.start()

    def _refresh_status(self):
        running = self._engine.is_running
        cfg     = self._engine.load_config()
        back    = cfg.get("backend", "?").capitalize()
        model   = cfg.get("model", "?")
        if running:
            self._dot.configure(text_color=SUCCESS)
            self._status_lbl.configure(text="Running", text_color=SUCCESS)
            self._toggle_btn.configure(text="Stop", fg_color=CARD2,
                                        hover_color=BDR, text_color=DANGER)
        else:
            self._dot.configure(text_color=DANGER)
            self._status_lbl.configure(text="Stopped", text_color=TEXT1)
            self._toggle_btn.configure(text="Start", fg_color="#ffffff",
                                        hover_color="#dddddd", text_color="#000000")
        self._backend_lbl.configure(text=f"{back}  ·  {model}")

    def _on_engine_event(self, event, **kwargs):
        self.after(0, self._handle, event, kwargs)

    def _handle(self, event, kw):
        if event in ("started", "stopped"):
            self._refresh_status()
        elif event == "processing":
            mode  = kw.get("mode", "?")
            chars = kw.get("chars", 0)
            self._add_row("...", f"[{mode}] Processing {chars} chars", TEXT3)
            self._stat_mode.configure(text=mode)
        elif event == "done":
            mode = kw.get("mode", "?")
            el   = kw.get("elapsed", 0)
            self._add_row("OK", f"[{mode}] Done in {el:.1f}s", SUCCESS)
            self._query_count += 1
            self._stat_count.configure(text=str(self._query_count))
            self._stat_time.configure(text=f"{el:.1f}s")
        elif event == "error":
            self._add_row("ERR", kw.get("msg", "Error"), DANGER)
        elif event == "log":
            self._add_row("·", kw.get("msg", ""), TEXT2)

    def _add_row(self, badge, text, color):
        now = datetime.now().strftime("%H:%M:%S")
        row = ctk.CTkFrame(self._feed, fg_color=CARD2, corner_radius=6)
        row.grid(row=len(self._feed_rows), column=0, sticky="ew", pady=(0, 4))
        row.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(row, text=badge, font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=color, width=32, anchor="center"
                     ).grid(row=0, column=0, padx=(8, 4), pady=8)
        ctk.CTkLabel(row, text=text[:90], font=ctk.CTkFont(size=11),
                     text_color=TEXT1, anchor="w"
                     ).grid(row=0, column=1, sticky="w", pady=8)
        ctk.CTkLabel(row, text=now, font=ctk.CTkFont(size=10),
                     text_color=TEXT2, width=56
                     ).grid(row=0, column=2, padx=8, pady=8)
        self._feed_rows.append(row)
        if len(self._feed_rows) > 40:
            self._feed_rows.pop(0).destroy()
