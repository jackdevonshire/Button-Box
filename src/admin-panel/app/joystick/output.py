"""
Sends key presses to Windows as if they came from a real keyboard, so games pick them up.
"""
import threading

import pydirectinput


def key_down(key):
    # _pause=False - pydirectinput otherwise sleeps 0.1s after every call, which would stall the joystick loop
    pydirectinput.keyDown(key, _pause=False)


def key_up(key):
    pydirectinput.keyUp(key, _pause=False)


class HeldKeys:
    """
    Tracks keys held on behalf of mappings. A key shared by several mappings (like Alt for free look on every hat
    direction) stays down until the last of them lets go, rather than flickering as the hat moves between directions.
    Holders are (owner, id) pairs, so the joystick and push-to-talk can share a key (like K) without letting go of
    each other's hold. Thread safe, as they run on different threads.
    """

    def __init__(self):
        self.__holders = {}
        self.__lock = threading.Lock()

    def press(self, key, holder):
        with self.__lock:
            holders = self.__holders.setdefault(key, set())
            if not holders:
                key_down(key)
            holders.add(holder)

    def release(self, key, holder):
        with self.__lock:
            holders = self.__holders.get(key)
            if not holders or holder not in holders:
                return
            holders.discard(holder)
            if not holders:
                key_up(key)

    def release_all(self, owner):
        """Lets go of everything one owner (e.g. "joystick") is holding"""
        with self.__lock:
            for key, holders in self.__holders.items():
                if not holders:
                    continue
                remaining = {holder for holder in holders if holder[0] != owner}
                if not remaining:
                    key_up(key)
                self.__holders[key] = remaining


# One set of held keys for everything that holds keys, so shared keys are only let go once nothing needs them
held_keys = HeldKeys()
