"""
Things that touch the PC itself rather than the button box: starting with Windows, the log file and opening the panel.
Used by both the tray app (main.py) and the settings page. Lives outside the app package so the tray can use it
without starting the whole app.
"""
import os
import sys
import webbrowser
import winreg

ADMIN_PANEL_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(ADMIN_PANEL_DIR, "admin-panel.log")
PORT = 80  # The button box always sends events to port 80
PANEL_URL = "http://localhost" if PORT == 80 else f"http://localhost:{PORT}"

STARTUP_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
STARTUP_VALUE = "ButtonBoxAdminPanel"


def startup_command():
    pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    return f'"{pythonw}" "{os.path.join(ADMIN_PANEL_DIR, "main.py")}" --background'


def starts_with_windows():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, STARTUP_KEY) as key:
            winreg.QueryValueEx(key, STARTUP_VALUE)
            return True
    except OSError:
        return False


def set_start_with_windows(enabled):
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, STARTUP_KEY, 0, winreg.KEY_SET_VALUE) as key:
        if enabled:
            winreg.SetValueEx(key, STARTUP_VALUE, 0, winreg.REG_SZ, startup_command())
        elif starts_with_windows():
            winreg.DeleteValue(key, STARTUP_VALUE)


def open_log():
    if os.path.exists(LOG_PATH):
        os.startfile(LOG_PATH)


def open_panel():
    # Prefer Chrome when it's installed, otherwise fall back to the default browser
    for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        try:
            with winreg.OpenKey(root, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe") as key:
                chrome = winreg.QueryValue(key, None)
            webbrowser.register("chrome", None, webbrowser.BackgroundBrowser(chrome))
            webbrowser.get("chrome").open(PANEL_URL)
            return
        except OSError:
            continue
    webbrowser.open(PANEL_URL)
