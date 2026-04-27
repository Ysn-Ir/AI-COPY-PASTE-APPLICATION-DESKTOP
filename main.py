"""
ClipboardAI Desktop App — Entry Point
"""

import sys
import threading
from pathlib import Path

# Ensure local app/ package is importable when run as a script
sys.path.insert(0, str(Path(__file__).parent))


def main():
    from app.engine import Engine
    from app.ui.window import MainWindow
    from app.tray import TrayApp

    engine = Engine()
    window = MainWindow(engine)

    # Run tray icon on its own daemon thread
    tray = TrayApp(engine, window)
    tray_thread = threading.Thread(target=tray.run, daemon=True)
    tray_thread.start()

    # Main UI loop (blocks until quit)
    window.mainloop()


if __name__ == "__main__":
    main()
