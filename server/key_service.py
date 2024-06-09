import time

from pynput.keyboard import Controller

from types import HttpStatusCode, NetworkResponse
from user_scripts import UserScripts


class KeyService:
    def __init__(self, configuration):
        self.keyboard = Controller()
        self.configuration = configuration
        self.current_configuration = configuration["Configurations"][0]
        self.user_script_service = UserScripts()

    def handle_key_event(self, button_reference, event):
        current_button_config = {}
        for button in self.current_configuration["Buttons"]:
            if button["Reference"] == button_reference:
                current_button_config = button
                break

        if len(current_button_config.items()) == 0:
            return NetworkResponse.with_error("Invalid Button Reference").with_status_code(
                HttpStatusCode.BadRequest).get()

        event_configuration = current_button_config[event]
        if event_configuration["Type"] == "Keybind":
            if event_configuration["ActionDuration"] == 0:
                self.keyboard.release(event_configuration["Action"])
            elif event_configuration["ActionDuration"] == None:
                self.keyboard.press(event_configuration["Action"])
            else:
                self.keyboard.press(event_configuration["Action"])
                time.sleep(event_configuration["ActionDuration"])
                self.keyboard.release(event_configuration["Action"])

        elif event_configuration["Type"] == "Method":
            self.user_script_service.call_script(event_configuration["Action"])

        return NetworkResponse.with_data({
            "ScreenMessage": event_configuration["ScreenMessage"],
            "ScreenDuration": event_configuration["ScreenDuration"]
        })

    def set_configuration(self, configuration_id):
        switched = False
        for configuration in self.configuration:
            if (configuration["Id"] == configuration_id):
                self.current_configuration = configuration
                switched = True
                break

        if not switched:
            return NetworkResponse.with_error("Invalid Configuration Id").with_status_code(
                HttpStatusCode.BadRequest).get()
