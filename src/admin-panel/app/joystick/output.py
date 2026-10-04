"""
Sends mouse movement and key presses to Windows as if they came from real devices, so games pick them up.
Mouse movement uses SendInput directly: relative moves arrive in games the same way a real mouse's do.
"""
import ctypes
from ctypes import wintypes

import pydirectinput

_user32 = ctypes.WinDLL("user32")

INPUT_MOUSE = 0
MOUSEEVENTF_MOVE = 0x0001


class _MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG), ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.c_size_t)]


class _INPUTUNION(ctypes.Union):
    # Sized for the largest member of the real union (MOUSEINPUT), which is all this sends
    _fields_ = [("mi", _MOUSEINPUT)]


class _INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("union", _INPUTUNION)]


def move_mouse(dx, dy):
    if dx == 0 and dy == 0:
        return
    event = _INPUT(type=INPUT_MOUSE, union=_INPUTUNION(mi=_MOUSEINPUT(dx=dx, dy=dy, dwFlags=MOUSEEVENTF_MOVE)))
    _user32.SendInput(1, ctypes.byref(event), ctypes.sizeof(_INPUT))


def key_down(key):
    # _pause=False - pydirectinput otherwise sleeps 0.1s after every call, which would stall the joystick loop
    pydirectinput.keyDown(key, _pause=False)


def key_up(key):
    pydirectinput.keyUp(key, _pause=False)


class HeldKeys:
    """
    Tracks keys held on behalf of mappings. A key shared by several mappings (like Alt for free look on every hat
    direction) stays down until the last of them lets go, rather than flickering as the hat moves between directions.
    """

    def __init__(self):
        self.__holders = {}

    def press(self, key, holder):
        holders = self.__holders.setdefault(key, set())
        if not holders:
            key_down(key)
        holders.add(holder)

    def release(self, key, holder):
        holders = self.__holders.get(key)
        if not holders or holder not in holders:
            return
        holders.discard(holder)
        if not holders:
            key_up(key)

    def release_all(self):
        for key, holders in self.__holders.items():
            if holders:
                key_up(key)
        self.__holders = {}
