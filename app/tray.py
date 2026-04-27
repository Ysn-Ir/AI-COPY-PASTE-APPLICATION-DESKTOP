"""
ClipboardAI — System Tray Icon
Uses pystray to provide a background tray icon with a right-click menu.
"""

import threading
from PIL import Image, ImageDraw


def _make_tray_icon() -> Image.Image:
    """Draw the tray icon programmatically (purple circle + clipboard)."""
    size = 64
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Purple filled circle
    draw.ellipse([2, 2, 62, 62], fill=(124, 58, 237, 255))

    # White clipboard body
    draw.rounded_rectangle([18, 22, 46, 52], radius=3, fill=(255, 255, 255, 230))

    # Clipboard clip (top center)
    draw.rounded_rectangle([24, 16, 40, 26], radius=3, fill=(200, 180, 250, 255))

    # Text lines on clipboard
    for y in [30, 36, 42]:
        w = 20 if y == 42 else 22
        draw.rectangle([22, y, 22 + w, y + 2], fill=(124, 58, 237, 200))

    # Small lightning bolt (top-right)
    bolt = [(50, 12), (44, 24), (50, 24), (42, 38), (50, 24), (56, 24), (50, 12)]
    draw.polygon(bolt, fill=(250, 220, 80, 240))

    return img


class TrayApp:
    def __init__(self, engine, window):
        self._engine = engine
        self._window = window

    def run(self) -> None:
        import pystray

        icon_img = _make_tray_icon()

        def on_open(icon, item):
            self._window.show()

        def on_toggle(icon, item):
            if self._engine.is_running:
                self._engine.stop()
            else:
                self._engine.start()
            icon.update_menu()

        def on_quit(icon, item):
            self._engine.stop()
            icon.stop()
            self._window.quit()

        def running_checked(item):
            return self._engine.is_running

        menu = pystray.Menu(
            pystray.MenuItem("Open ClipboardAI", on_open, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Running", on_toggle, checked=running_checked),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", on_quit),
        )

        self._icon = pystray.Icon(
            "ClipboardAI",
            icon_img,
            "ClipboardAI",
            menu,
        )
        self._icon.run()
