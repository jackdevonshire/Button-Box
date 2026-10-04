"""
Reads joysticks through Windows' built-in multimedia joystick API (WinMM). It needs no drivers or extra packages and
keeps working while a game has focus, which the panel needs as it runs in the background.
"""
import ctypes
import winreg
from ctypes import wintypes

_winmm = ctypes.WinDLL("winmm")

MAX_DEVICES = 16
JOY_RETURNALL = 0xFF
JOYCAPS_HASPOV = 0x10
POV_CENTERED = 0xFFFF
AXIS_MAX = 65535


class _JOYCAPSW(ctypes.Structure):
    _fields_ = [("wMid", wintypes.WORD), ("wPid", wintypes.WORD), ("szPname", wintypes.WCHAR * 32),
                ("wXmin", wintypes.UINT), ("wXmax", wintypes.UINT), ("wYmin", wintypes.UINT),
                ("wYmax", wintypes.UINT), ("wZmin", wintypes.UINT), ("wZmax", wintypes.UINT),
                ("wNumButtons", wintypes.UINT), ("wPeriodMin", wintypes.UINT), ("wPeriodMax", wintypes.UINT),
                ("wRmin", wintypes.UINT), ("wRmax", wintypes.UINT), ("wUmin", wintypes.UINT),
                ("wUmax", wintypes.UINT), ("wVmin", wintypes.UINT), ("wVmax", wintypes.UINT),
                ("wCaps", wintypes.UINT), ("wMaxAxes", wintypes.UINT), ("wNumAxes", wintypes.UINT),
                ("wMaxButtons", wintypes.UINT), ("szRegKey", wintypes.WCHAR * 32),
                ("szOEMVxD", wintypes.WCHAR * 260)]


class _JOYINFOEX(ctypes.Structure):
    _fields_ = [(name, wintypes.DWORD) for name in (
        "dwSize", "dwFlags", "dwXpos", "dwYpos", "dwZpos", "dwRpos", "dwUpos", "dwVpos", "dwButtons",
        "dwButtonNumber", "dwPOV", "dwReserved1", "dwReserved2")]


class JoystickDevice:
    def __init__(self, index, vendor_id, product_id, name, axes, buttons, has_hat):
        self.index = index
        self.id = f"{vendor_id:04X}:{product_id:04X}"  # Stable across reconnects, unlike the index
        self.name = name
        self.axes = axes
        self.buttons = buttons
        self.has_hat = has_hat

    def to_json(self):
        return {"id": self.id, "name": self.name, "axes": self.axes, "buttons": self.buttons, "hasHat": self.has_hat}


class JoystickState:
    def __init__(self, pov, buttons, axes):
        self.pov = pov          # Hat angle in hundredths of a degree clockwise from up, or None when centred
        self.buttons = buttons  # Set of pressed button numbers, starting at 1
        self.axes = axes        # Axis name -> position from -1 to 1

    @property
    def hat_directions(self):
        """The hat's directions - two at once on a diagonal - as a set of up/down/left/right"""
        if self.pov is None:
            return set()
        angle = self.pov / 100
        directions = set()
        if angle < 67.5 or angle > 292.5:
            directions.add("up")
        if 22.5 < angle < 157.5:
            directions.add("right")
        if 112.5 < angle < 247.5:
            directions.add("down")
        if 202.5 < angle < 337.5:
            directions.add("left")
        return directions


def _oem_name(vendor_id, product_id):
    # Windows keeps the product's real name here - the WinMM name is a generic driver name
    path = rf"System\CurrentControlSet\Control\MediaProperties\PrivateProperties\Joystick\OEM\VID_{vendor_id:04X}&PID_{product_id:04X}"
    for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        try:
            with winreg.OpenKey(root, path) as key:
                name = winreg.QueryValueEx(key, "OEMName")[0]
                if name:
                    return name
        except OSError:
            continue
    return None


def list_devices():
    devices = []
    for index in range(MAX_DEVICES):
        info = _JOYINFOEX(dwSize=ctypes.sizeof(_JOYINFOEX), dwFlags=JOY_RETURNALL)
        if _winmm.joyGetPosEx(index, ctypes.byref(info)) != 0:
            continue  # Nothing connected at this index
        caps = _JOYCAPSW()
        if _winmm.joyGetDevCapsW(index, ctypes.byref(caps), ctypes.sizeof(caps)) != 0:
            continue
        name = _oem_name(caps.wMid, caps.wPid) or f"Joystick {index + 1}"
        devices.append(JoystickDevice(index, caps.wMid, caps.wPid, name, caps.wNumAxes, caps.wNumButtons,
                                      bool(caps.wCaps & JOYCAPS_HASPOV)))
    return devices


def read_state(index):
    """Reads a joystick's current state, or returns None if it's been disconnected"""
    info = _JOYINFOEX(dwSize=ctypes.sizeof(_JOYINFOEX), dwFlags=JOY_RETURNALL)
    if _winmm.joyGetPosEx(index, ctypes.byref(info)) != 0:
        return None

    def axis(value):
        return round(value / AXIS_MAX * 2 - 1, 3)

    buttons = {bit + 1 for bit in range(32) if info.dwButtons & (1 << bit)}
    pov = None if info.dwPOV == POV_CENTERED else info.dwPOV
    return JoystickState(pov, buttons, {"x": axis(info.dwXpos), "y": axis(info.dwYpos), "z": axis(info.dwZpos),
                                        "r": axis(info.dwRpos)})
