from app.integrations.integration import BaseIntegrationService
from app.core.models import IntegrationAction
from app.core.display_service import DisplayService
from app.core.button_box_service import ButtonBoxService
from app.core.types import HttpStatusCode, NetworkResponse
import pydirectinput
import time
import threading

KEY_TYPES = {
    "tap": "Tap",
    "infinite": "Hold down",
    "off": "Release",
    "toggle": "Toggle hold",
}

class KeyboardService(BaseIntegrationService):
    def __init__(self):
        super().__init__()
        # Core details - must be present for EVERY integration
        self.id = 1
        self.name = "Keyboard"
        self.description = "Press keys and shortcuts on this PC"
        self.is_active = True
        self.configuration = {}

        self.ui_icon = "keyboard"
        self.action_editor = "keyboard"

        self.held_keys = set()

    def initialise_service(self):
        pass

    def describe(self):
        description = super().describe()
        description["options"] = {
            "keys": sorted(set(pydirectinput.KEYBOARD_MAPPING)),
            "types": [{"value": value, "label": label} for value, label in KEY_TYPES.items()],
        }
        return description

    def validate_action_configuration(self, configuration):
        if not isinstance(configuration, list) or len(configuration) == 0:
            raise ValueError("Add at least one key")

        cleaned = []
        for entry in configuration:
            key = str(entry.get("key", "")).lower() if isinstance(entry, dict) else ""
            key_type = entry.get("type") if isinstance(entry, dict) else None
            if key not in pydirectinput.KEYBOARD_MAPPING:
                raise ValueError(f"'{key}' isn't a key that can be pressed")
            if key_type not in KEY_TYPES:
                raise ValueError(f"'{key_type}' isn't a valid key type")
            cleaned.append({"key": key, "type": key_type})
        return cleaned

    def handle_action(self, action: IntegrationAction, display: DisplayService, button_box: ButtonBoxService):
        config = action.configuration
        # Letting go of held keys (e.g. when a button is released) isn't worth flashing up on the screen
        if any(key_duration["type"] != "off" for key_duration in config):
            display.display_temporary_message(["", action.name, "", ""], 2)

        for key_duration in config:
            key = key_duration["key"]
            duration = key_duration["type"]

            if duration == "tap": # Tap each key for a second
                threading.Thread(target=self.tap_key, args=(key,)).start()
            elif duration == "off":
                if key in self.held_keys:
                    pydirectinput.keyUp(key)
                    self.held_keys.remove(key)
            elif duration == "infinite":
                if key not in self.held_keys:
                    pydirectinput.keyDown(key)
                    self.held_keys.add(key)
            elif duration == "toggle":
                if key in self.held_keys:
                    pydirectinput.keyUp(key)
                    self.held_keys.remove(key)
                else:
                    pydirectinput.keyDown(key)
                    self.held_keys.add(key)

        return NetworkResponse()

    def tap_key(self, key):
        pydirectinput.keyDown(key)
        time.sleep(0.5)
        pydirectinput.keyUp(key)