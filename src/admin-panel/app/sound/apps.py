"""
Which app is in front, so push-to-talk only holds its key while the game is focused (rather than typing k's into
Discord when you alt-tab and talk).
"""
import ctypes
import os
from ctypes import wintypes

_user32 = ctypes.WinDLL("user32")
_kernel32 = ctypes.WinDLL("kernel32")

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
_EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


def _process_name(hwnd):
    pid = wintypes.DWORD()
    _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    process = _kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
    if not process:
        return None
    try:
        size = wintypes.DWORD(1024)
        buffer = ctypes.create_unicode_buffer(size.value)
        if not _kernel32.QueryFullProcessImageNameW(process, 0, buffer, ctypes.byref(size)):
            return None
        return os.path.basename(buffer.value)
    finally:
        _kernel32.CloseHandle(process)


def _title(hwnd):
    length = _user32.GetWindowTextLengthW(hwnd)
    buffer = ctypes.create_unicode_buffer(length + 1)
    _user32.GetWindowTextW(hwnd, buffer, length + 1)
    return buffer.value


def foreground_app():
    """The exe name of the app in front, e.g. "Wardogs.exe", or None"""
    hwnd = _user32.GetForegroundWindow()
    return _process_name(hwnd) if hwnd else None


def running_apps():
    """Apps with a visible window, to choose from - [{"exe", "title"}], one per app"""
    apps = {}

    def visit(hwnd, _):
        if _user32.IsWindowVisible(hwnd) and _user32.GetWindowTextLengthW(hwnd) > 0:
            name = _process_name(hwnd)
            if name and name.lower() not in apps:
                apps[name.lower()] = {"exe": name, "title": _title(hwnd)}
        return True

    _user32.EnumWindows(_EnumWindowsProc(visit), 0)
    return sorted(apps.values(), key=lambda app: app["exe"].lower())
