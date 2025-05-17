from flask import Blueprint
from app.integrations.integration import BaseIntegrationService
from app.core.models import IntegrationAction
from app.core.display_service import DisplayService
from app.core.button_box_service import ButtonBoxService
from app.core.types import HttpStatusCode, NetworkResponse
import pydirectinput
import time
import threading

class KeyboardService(BaseIntegrationService):
    def __init__(self):
        # Core details - must be present for EVERY integration
        self.id = 1
        self.name = "Keyboard"
        self.description = "An integration to simulate keyboard interactions on the server hosts machine"
        self.is_active = True  # TODO in future, add an integration manager so we can delete this and just manage on a web page
        self.configuration = {}

        self.url_prefix = "/integration/keyboard"
        self.blueprint = Blueprint('bp_keyboard', __name__, url_prefix=self.url_prefix)
        self.icon = "fas fa-keyboard"

        self.held_keys = set()

    def initialise_service(self):
        pass

    def handle_action(self, action: IntegrationAction, display: DisplayService, button_box: ButtonBoxService):
        display.display_temporary_message(["", action.name, "", ""], 2)
        config = action.configuration

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

        return NetworkResponse()

    def tap_key(self, key):
        pydirectinput.keyDown(key)
        time.sleep(0.5)
        pydirectinput.keyUp(key)