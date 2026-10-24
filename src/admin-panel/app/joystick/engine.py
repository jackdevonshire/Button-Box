"""
The joystick engine: reads connected joysticks in a background loop and applies the active configuration's mappings,
turning hat directions and buttons into held keys or actions.
"""
import threading
import time
import traceback

from app.joystick import output, winmm

TICK_SECONDS = 1 / 250             # How often joysticks are read
DEVICE_REFRESH_SECONDS = 2         # How often to look for joysticks being plugged in or removed
AXIS_PUBLISH_SECONDS = 0.1         # Axis changes are sent to the UI at most this often


class JoystickEngine:
    def __init__(self, event_bus, is_enabled, run_action):
        self.__event_bus = event_bus
        self.__is_enabled = is_enabled
        self.__run_action = run_action

        self.__devices = {}            # Device id -> winmm.JoystickDevice
        self.__states = {}             # Device id -> latest winmm.JoystickState
        self.__mappings = []           # The active configuration's enabled mappings, as plain dicts
        self.__active_inputs = set()   # (device, input_type, input) currently held
        self.__held = output.held_keys
        self.__lock = threading.Lock()
        self.__last_device_refresh = 0
        self.__last_axis_publish = 0
        self.__published_axes = {}

    def start(self):
        threading.Thread(target=self.__run, name="joystick-engine", daemon=True).start()

    def set_mappings(self, mappings):
        """Replaces the mappings in use, e.g. when the configuration changes. Anything held is let go first."""
        with self.__lock:
            self.__release_everything()
            self.__mappings = [mapping for mapping in mappings if mapping["enabled"]]

    def stop_outputs(self):
        with self.__lock:
            self.__release_everything()

    def snapshot(self):
        with self.__lock:
            return {
                "devices": [device.to_json() for device in self.__devices.values()],
                "states": {device_id: self.__state_json(state) for device_id, state in self.__states.items()},
            }

    # region Loop

    def __run(self):
        while True:
            started = time.perf_counter()
            try:
                with self.__lock:
                    self.__tick(started)
            except Exception:
                print(f"Joystick engine error:\n{traceback.format_exc()}")
                time.sleep(1)
            time.sleep(max(0.0, TICK_SECONDS - (time.perf_counter() - started)))

    def __tick(self, now):
        if now - self.__last_device_refresh > DEVICE_REFRESH_SECONDS:
            self.__refresh_devices()
            self.__last_device_refresh = now

        changed = False
        for device_id, device in list(self.__devices.items()):
            state = winmm.read_state(device.index)
            if state is None:
                # Unplugged - forget it, and the next refresh will pick it up again if it comes back
                self.__devices.pop(device_id)
                self.__states.pop(device_id, None)
                changed = True
                continue
            previous = self.__states.get(device_id)
            self.__states[device_id] = state
            if previous is None or previous.pov != state.pov or previous.buttons != state.buttons:
                changed = True

        if changed:
            self.__publish_state()
        elif now - self.__last_axis_publish > AXIS_PUBLISH_SECONDS and self.__axes_moved():
            self.__publish_state()

        if self.__is_enabled():
            self.__apply_mappings()
        elif self.__active_inputs:
            self.__release_everything()

    def __refresh_devices(self):
        devices = {device.id: device for device in winmm.list_devices()}
        if devices.keys() != self.__devices.keys():
            added = devices.keys() - self.__devices.keys()
            for device_id in added:
                self.__event_bus.log("system", f"Joystick connected: {devices[device_id].name}")
            self.__devices = devices
            self.__publish_state()
        else:
            self.__devices = devices

    # endregion

    # region Mappings

    def __current_inputs(self):
        inputs = set()
        for device_id, state in self.__states.items():
            inputs |= {(device_id, "hat", direction) for direction in state.hat_directions}
            inputs |= {(device_id, "button", str(button)) for button in state.buttons}
        return inputs

    def __apply_mappings(self):
        inputs = self.__current_inputs()
        pressed = inputs - self.__active_inputs
        released = self.__active_inputs - inputs
        self.__active_inputs = inputs

        for mapping in self.__mappings:
            key = (mapping["device"], mapping["inputType"], mapping["input"])
            if key in pressed:
                self.__on_press(mapping)
            elif key in released:
                self.__on_release(mapping)

    def __on_press(self, mapping):
        settings = mapping["output"]
        if mapping["outputType"] == "keys":
            for key in settings.get("keys", []):
                self.__held.press(key, ("joystick", mapping["id"]))
        elif mapping["outputType"] == "action" and settings.get("when", "press") == "press":
            self.__trigger_action(mapping)

    def __on_release(self, mapping):
        settings = mapping["output"]
        if mapping["outputType"] == "keys":
            for key in settings.get("keys", []):
                self.__held.release(key, ("joystick", mapping["id"]))
        elif mapping["outputType"] == "action" and settings.get("when", "press") == "release":
            self.__trigger_action(mapping)

    def __trigger_action(self, mapping):
        action_id = mapping["output"].get("actionId")
        if action_id:
            self.__run_action(action_id, mapping)

    def __release_everything(self):
        self.__held.release_all("joystick")
        self.__active_inputs = set()

    # endregion

    # region Publishing live state to the UI

    def __axes_moved(self):
        for device_id, state in self.__states.items():
            previous = self.__published_axes.get(device_id, {})
            if any(abs(value - previous.get(axis, 0)) > 0.01 for axis, value in state.axes.items()):
                return True
        return False

    def __publish_state(self):
        self.__last_axis_publish = time.perf_counter()
        self.__published_axes = {device_id: dict(state.axes) for device_id, state in self.__states.items()}
        self.__event_bus.publish("joystick", {
            "devices": [device.to_json() for device in self.__devices.values()],
            "states": {device_id: self.__state_json(state) for device_id, state in self.__states.items()},
        })

    @staticmethod
    def __state_json(state):
        return {
            "hat": sorted(state.hat_directions),
            "buttons": sorted(state.buttons),
            "axes": state.axes,
        }

    # endregion
