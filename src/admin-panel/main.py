"""
Runs the admin panel server in the background with a system tray icon.

    pythonw main.py                 Start (or, if already running, just open the panel)
    pythonw main.py --background    Start without opening the panel (used when starting with Windows)
"""
import ctypes
import logging
import os
import sys
import threading

import requests

from desktop import (LOG_PATH, PANEL_URL, PORT, STARTUP_VALUE, open_log, open_panel, set_start_with_windows,
                     starts_with_windows)

MAX_LOG_BYTES = 5 * 1024 * 1024
APP_NAME = "Button Box Admin Panel"


class Tee:
    """Writes output to the log file, and to the console too when there is one"""

    def __init__(self, *streams):
        self.streams = [s for s in streams if s is not None]

    def write(self, data):
        for stream in self.streams:
            stream.write(data)
            stream.flush()

    def flush(self):
        for stream in self.streams:
            stream.flush()


def setup_logging():
    if os.path.exists(LOG_PATH) and os.path.getsize(LOG_PATH) > MAX_LOG_BYTES:
        os.replace(LOG_PATH, LOG_PATH + ".old")
    log_file = open(LOG_PATH, "a", encoding="utf-8", buffering=1)
    sys.stdout = Tee(log_file, sys.__stdout__)
    sys.stderr = Tee(log_file, sys.__stderr__)

    # Skip a log line for every request (the panel polls for status) but keep warnings and errors
    logging.getLogger("werkzeug").setLevel(logging.WARNING)


def show_error(message):
    ctypes.windll.user32.MessageBoxW(None, message, APP_NAME, 0x10)


def is_panel_running():
    try:
        # 127.0.0.1 rather than localhost - localhost tries IPv6 first, which the server doesn't listen on
        return "activeConfigurationId" in requests.get(f"http://127.0.0.1:{PORT}/api/status", timeout=2).json()
    except (requests.RequestException, ValueError):
        return False


def create_icon_image():
    from PIL import Image, ImageDraw

    # A tiny version of the panel: dark plate, a row of buttons and a red protected switch
    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((2, 8, 62, 56), radius=8, fill=(32, 32, 36))
    draw.rectangle((10, 15, 40, 27), fill=(55, 138, 221))
    for x in (10, 22, 34):
        draw.ellipse((x, 35, x + 8, 43), fill=(220, 220, 220))
    draw.rectangle((47, 15, 55, 47), fill=(226, 75, 74))
    return image


def run_tray(server):
    import pystray
    from app import button_box_service

    def status_text(_):
        status = button_box_service.monitor.get_status()
        if status["Scanning"]:
            return "Box: searching network..."
        if status["Online"]:
            return f"Box: online ({status['ButtonBoxIP']})"
        return "Box: offline"

    def quit_app(icon, _):
        icon.stop()
        server.shutdown()

    icon = pystray.Icon(STARTUP_VALUE, create_icon_image(), APP_NAME, menu=pystray.Menu(
        pystray.MenuItem("Open panel", lambda: open_panel(), default=True),
        pystray.MenuItem(status_text, None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Start with Windows", lambda: set_start_with_windows(not starts_with_windows()),
                         checked=lambda _: starts_with_windows()),
        pystray.MenuItem("Open log", lambda: open_log()),
        pystray.MenuItem("Quit", quit_app),
    ))

    def refresh_status():
        # The tray menu is only rebuilt when asked, so refresh it to keep the status line current
        while True:
            threading.Event().wait(5)
            icon.title = f"{APP_NAME} - {status_text(None)}"
            icon.update_menu()

    threading.Thread(target=refresh_status, name="tray-refresh", daemon=True).start()
    icon.run()


def main():
    setup_logging()
    background = "--background" in sys.argv

    if is_panel_running():
        if not background:
            open_panel()
        return

    try:
        from werkzeug.serving import make_server
        from app import app
        server = make_server("0.0.0.0", PORT, app, threaded=True)
    except OSError as e:
        print(f"Failed to start server: {e}")
        show_error(f"Couldn't start the admin panel on port {PORT} - another program may be using it.\n\n{e}")
        return
    except Exception:
        import traceback
        traceback.print_exc()
        show_error(f"The admin panel failed to start. See the log for details:\n{LOG_PATH}")
        return

    threading.Thread(target=server.serve_forever, name="web-server", daemon=True).start()
    print(f"Admin panel running at {PANEL_URL}")
    if not background:
        open_panel()

    run_tray(server)


if __name__ == "__main__":
    main()
