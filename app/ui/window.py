"""
ClipboardAI — Main Window
Black/gray/white design with geometric dot-grid background.
Hides to tray on close instead of quitting.
"""

import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageDraw, ImageTk

from .panel_dashboard import DashboardPanel
from .panel_api_keys  import ApiKeysPanel
from .panel_settings  import SettingsPanel
from .panel_modes     import ModesPanel
from .panel_log       import LogPanel

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# ── Palette ────────────────────────────────────────────────────────────────
BG      = "#0a0a0a"
SIDEBAR = "#0e0e0e"
CARD    = "#141414"
BDR     = "#2a2a2a"
TEXT1   = "#f0f0f0"
TEXT2   = "#555555"
TEXT_A  = "#888888"
SUCCESS = "#22c55e"
DANGER  = "#ef4444"

NAV_ITEMS = [
    ("Dashboard",  "◈"),
    ("API Keys",   "⬡"),
    ("Settings",   "◉"),
    ("Modes",      "◧"),
    ("Log",        "≡"),
]


def _make_geo_bg(width: int, height: int) -> Image.Image:
    """Generates a dot-grid + diagonal-lines geometric background."""
    img  = Image.new("RGB", (width, height), "#080808")
    draw = ImageDraw.Draw(img)

    # Subtle dot grid
    step = 36
    for x in range(0, width + step, step):
        for y in range(0, height + step, step):
            draw.ellipse([x - 1, y - 1, x + 1, y + 1], fill="#151515")

    # Thin diagonal lines — top-left corner accent
    for i in range(-100, 350, 48):
        draw.line([(i, 0), (i + 260, 260)], fill="#111111", width=1)

    # Thin diagonal lines — bottom-right corner accent
    for i in range(-100, 350, 48):
        draw.line([(width - i, height), (width - i - 260, height - 260)],
                  fill="#111111", width=1)

    return img


class MainWindow(ctk.CTk):
    def __init__(self, engine):
        super().__init__()
        self._engine = engine
        self._panels: dict = {}
        self._nav_btns: list = []
        self._active_panel = None
        self._bg_photo = None
        self._bg_label = None

        self.title("ClipboardAI")
        self.geometry("980x660")
        self.minsize(860, 560)
        self.configure(fg_color=BG)
        self.protocol("WM_DELETE_WINDOW", self.hide)

        self._setup_bg()
        self._build()
        self._show_panel("Dashboard")

        self._engine.add_callback(self._on_engine_event)
        self._engine.start()

        cfg = self._engine.load_config()
        if cfg.get("start_minimized", False):
            self.after(150, self.hide)

    # ── Geometric background ───────────────────────────────────────────────

    def _setup_bg(self):
        """Place a background label behind everything for the dot-grid pattern."""
        self._bg_label = tk.Label(self, bg="#080808", bd=0, highlightthickness=0)
        self._bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        # Lower it below all other widgets
        self._bg_label.lower()
        self.bind("<Configure>", self._on_resize)

    def _on_resize(self, event=None):
        self.after_idle(self._redraw_bg)

    def _redraw_bg(self):
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 10 or h < 10:
            return
        img   = _make_geo_bg(w, h)
        photo = ImageTk.PhotoImage(img)
        self._bg_photo = photo  # keep reference
        self._bg_label.configure(image=photo)

    # ── Layout ─────────────────────────────────────────────────────────────

    def _build(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ── Sidebar ────────────────────────────────────────────────────────
        sidebar = ctk.CTkFrame(self, fg_color=SIDEBAR, width=216,
                               corner_radius=0, border_width=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_columnconfigure(0, weight=1)
        sidebar.grid_rowconfigure(8, weight=1)

        # Logo
        logo = ctk.CTkFrame(sidebar, fg_color="transparent")
        logo.grid(row=0, column=0, sticky="ew", padx=20, pady=(28, 20))
        ctk.CTkLabel(logo, text="ClipboardAI",
                     font=ctk.CTkFont(size=17, weight="bold"),
                     text_color=TEXT1).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(logo, text="AI Clipboard Assistant",
                     font=ctk.CTkFont(size=10), text_color=TEXT2
                     ).grid(row=1, column=0, sticky="w")

        # Divider
        ctk.CTkFrame(sidebar, fg_color=BDR, height=1
                     ).grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 10))

        # Nav buttons
        for i, (label, icon) in enumerate(NAV_ITEMS):
            btn = ctk.CTkButton(
                sidebar,
                text=f"  {icon}   {label}",
                anchor="w",
                height=42,
                corner_radius=8,
                fg_color="transparent",
                text_color=TEXT_A,
                hover_color=CARD,
                font=ctk.CTkFont(size=13),
                border_width=0,
                command=lambda l=label: self._show_panel(l),
            )
            btn.grid(row=i + 2, column=0, sticky="ew", padx=10, pady=2)
            self._nav_btns.append((label, btn))

        # Divider at bottom
        ctk.CTkFrame(sidebar, fg_color=BDR, height=1
                     ).grid(row=8, column=0, sticky="ew", padx=16, pady=(0, 10))

        # Status pill
        self._status_pill = ctk.CTkLabel(
            sidebar, text="● Stopped",
            font=ctk.CTkFont(size=11), text_color=DANGER,
            fg_color=CARD, corner_radius=8,
        )
        self._status_pill.grid(row=9, column=0, sticky="ew", padx=16, pady=(0, 20))

        # ── Content area ───────────────────────────────────────────────────
        content = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        content.grid(row=0, column=1, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=1)

        # Build panels
        self._panels["Dashboard"] = DashboardPanel(content, self._engine)
        self._panels["API Keys"]  = ApiKeysPanel(content, self._engine)
        self._panels["Settings"]  = SettingsPanel(content, self._engine)
        self._panels["Modes"]     = ModesPanel(content, self._engine)
        self._panels["Log"]       = LogPanel(content, self._engine)

        for panel in self._panels.values():
            panel.grid(row=0, column=0, sticky="nsew")
            panel.grid_remove()

    # ── Navigation ─────────────────────────────────────────────────────────

    def _show_panel(self, label: str):
        if self._active_panel:
            self._panels[self._active_panel].grid_remove()
        for lbl, btn in self._nav_btns:
            if lbl == label:
                btn.configure(fg_color=CARD, text_color=TEXT1,
                              border_width=1, border_color=BDR)
            else:
                btn.configure(fg_color="transparent", text_color=TEXT_A,
                              border_width=0)
        self._panels[label].grid()
        self._active_panel = label

    # ── Show / hide ────────────────────────────────────────────────────────

    def show(self):
        self.deiconify()
        self.lift()
        self.focus_force()

    def hide(self):
        self.withdraw()

    # ── Engine events ──────────────────────────────────────────────────────

    def _on_engine_event(self, event, **kwargs):
        self.after(0, self._update_pill, event)

    def _update_pill(self, event):
        if event == "started":
            self._status_pill.configure(text="● Running", text_color=SUCCESS)
        elif event == "stopped":
            self._status_pill.configure(text="● Stopped", text_color=DANGER)
