"""
Global keyboard shortcuts for sounds, through Windows' RegisterHotKey - the same way apps like Discord and OBS do it.
Nothing is sent or simulated: Windows tells the panel when a shortcut is pressed, in any app. The app in front doesn't
see that key combination, so shortcuts should be ones the game doesn't use.

Keys use the panel's key names (as recorded in the UI), e.g. ["ctrlleft", "f1"] or ["num5"].
"""
import ctypes
import threading
from ctypes import wintypes

_user32 = ctypes.WinDLL("user32")
_kernel32 = ctypes.WinDLL("kernel32")

WM_HOTKEY = 0x0312
WM_APP = 0x8000
PM_NOREMOVE = 0
MOD_ALT, MOD_CONTROL, MOD_SHIFT, MOD_WIN, MOD_NOREPEAT = 0x1, 0x2, 0x4, 0x8, 0x4000
APPLY_TIMEOUT_SECONDS = 2

MODIFIERS = {
    "ctrl": MOD_CONTROL, "ctrlleft": MOD_CONTROL, "ctrlright": MOD_CONTROL,
    "shift": MOD_SHIFT, "shiftleft": MOD_SHIFT, "shiftright": MOD_SHIFT,
    "alt": MOD_ALT, "altleft": MOD_ALT, "altright": MOD_ALT,
    "win": MOD_WIN, "winleft": MOD_WIN, "winright": MOD_WIN,
}
MODIFIER_LABELS = [(MOD_CONTROL, "Ctrl"), (MOD_SHIFT, "Shift"), (MOD_ALT, "Alt"), (MOD_WIN, "Win")]

# Windows virtual key codes for the panel's key names
VIRTUAL_KEYS = {
    **{chr(code).lower(): code for code in range(ord("A"), ord("Z") + 1)},
    **{str(digit): ord(str(digit)) for digit in range(10)},
    **{f"f{number}": 0x6F + number for number in range(1, 25)},
    **{f"num{digit}": 0x60 + digit for digit in range(10)},
    "multiply": 0x6A, "add": 0x6B, "subtract": 0x6D, "decimal": 0x6E, "divide": 0x6F,
    "space": 0x20, "enter": 0x0D, "esc": 0x1B, "tab": 0x09, "backspace": 0x08,
    "insert": 0x2D, "delete": 0x2E, "home": 0x24, "end": 0x23, "pageup": 0x21, "pagedown": 0x22,
    "up": 0x26, "down": 0x28, "left": 0x25, "right": 0x27,
    "printscreen": 0x2C, "scrolllock": 0x91, "pause": 0x13, "capslock": 0x14, "numlock": 0x90, "apps": 0x5D,
    ";": 0xBA, "=": 0xBB, ",": 0xBC, "-": 0xBD, ".": 0xBE, "/": 0xBF, "`": 0xC0, "[": 0xDB, "\\": 0xDC, "]": 0xDD,
    "'": 0xDE,
}
SUPPORTED_KEYS = sorted(set(MODIFIERS) | set(VIRTUAL_KEYS))
KEY_LABELS = {"pageup": "Page Up", "pagedown": "Page Down", "printscreen": "Print Screen", "scrolllock": "Scroll Lock",
              "capslock": "Caps Lock", "numlock": "Num Lock", "apps": "Menu", "multiply": "Num *", "add": "Num +",
              "subtract": "Num -", "decimal": "Num .", "divide": "Num /"}


def parse(keys):
    """
    A shortcut's (modifier flags, virtual key), raising ValueError with a message for the user if it isn't one.
    A shortcut is any number of Ctrl/Shift/Alt/Win plus exactly one other key.
    """
    if not isinstance(keys, list) or not keys or not all(isinstance(key, str) for key in keys):
        raise ValueError("Press a key or combination for the shortcut")
    modifiers = 0
    others = []
    for key in keys:
        if key in MODIFIERS:
            modifiers |= MODIFIERS[key]
        elif key in VIRTUAL_KEYS:
            others.append(key)
        else:
            raise ValueError(f"'{key}' can't be used in a shortcut")
    if len(others) != 1:
        raise ValueError("A shortcut needs one key besides Ctrl, Shift, Alt or Win")
    return modifiers, VIRTUAL_KEYS[others[0]]


def label(keys):
    """A readable shortcut, e.g. "Ctrl+F1" """
    modifiers, _ = parse(keys)
    key = next(key for key in keys if key not in MODIFIERS)
    if key.startswith("num") and key[3:].isdigit():
        name = f"Num {key[3:]}"
    elif key in KEY_LABELS:
        name = KEY_LABELS[key]
    elif len(key) == 1 or (key.startswith("f") and key[1:].isdigit()):
        name = key.upper()
    else:
        name = key.capitalize()
    return "+".join([text for flag, text in MODIFIER_LABELS if modifiers & flag] + [name])


class _MSG(ctypes.Structure):
    _fields_ = [("hwnd", wintypes.HWND), ("message", wintypes.UINT), ("wParam", wintypes.WPARAM),
                ("lParam", wintypes.LPARAM), ("time", wintypes.DWORD), ("pt", wintypes.POINT)]


class HotkeyListener:
    """
    Registers shortcuts and calls on_hotkey(id) when one is pressed. Windows ties hotkeys to the thread that registered
    them, so a dedicated thread registers them and waits for presses.
    """

    def __init__(self, on_hotkey):
        self.__on_hotkey = on_hotkey
        self.__wanted = {}            # Id -> keys
        self.errors = {}              # Id -> why its shortcut couldn't be registered
        self.__thread_id = None
        self.__ready = threading.Event()
        self.__applied = threading.Event()
        self.__lock = threading.Lock()

    def start(self):
        threading.Thread(target=self.__run, name="sound-hotkeys", daemon=True).start()
        self.__ready.wait(APPLY_TIMEOUT_SECONDS)

    def set(self, shortcuts):
        """Replaces the registered shortcuts with {id: keys}, waiting until Windows has them"""
        with self.__lock:
            self.__wanted = dict(shortcuts)
            self.__applied.clear()
            if self.__thread_id is not None:
                _user32.PostThreadMessageW(self.__thread_id, WM_APP, 0, 0)
                self.__applied.wait(APPLY_TIMEOUT_SECONDS)

    def __run(self):
        self.__thread_id = _kernel32.GetCurrentThreadId()
        message = _MSG()
        _user32.PeekMessageW(ctypes.byref(message), None, 0, 0, PM_NOREMOVE)  # Creates this thread's message queue
        self.__ready.set()

        registered = set()
        while _user32.GetMessageW(ctypes.byref(message), None, 0, 0) > 0:
            if message.message == WM_HOTKEY:
                try:
                    self.__on_hotkey(int(message.wParam))
                except Exception as e:
                    print(f"Sound - shortcut failed: {e}")
            elif message.message == WM_APP:
                for id in registered:
                    _user32.UnregisterHotKey(None, id)
                registered.clear()
                errors = {}
                for id, keys in self.__wanted.items():
                    modifiers, key = parse(keys)
                    if _user32.RegisterHotKey(None, id, modifiers | MOD_NOREPEAT, key):
                        registered.add(id)
                    else:
                        errors[id] = "Another app is already using this shortcut"
                self.errors = errors
                self.__applied.set()
