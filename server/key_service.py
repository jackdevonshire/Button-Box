import time

from flask import make_response, jsonify
from pynput.keyboard import Controller
from user_scripts import UserScripts


class KeyService:
    def __init__(self, configurations):
        self.keyboard = Controller()
        self.user_script_service = UserScripts()
        self.configurations = configurations
        self.current_configuration = self.configurations[0]

    def handle_key_event(self, button_reference, event):
        current_button_config = {}
        for button in self.current_configuration["Buttons"]:
            if button["Reference"] == button_reference:
                current_button_config = button
                break

        if len(current_button_config.items()) == 0:
            return make_response(jsonify({
                "ScreenMessage": ["", "Error:", "Invalid Button", button_reference],
                "ScreenDuration": 2
            }))

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

        return make_response(jsonify({
            "ScreenMessage": event_configuration["ScreenMessage"],
            "ScreenDuration": event_configuration["ScreenDuration"]
        }))

    def switch_configuration(self):
        # Switch to next configuration
        for x in range(0, len(self.configurations) - 1):
            if self.configurations[x] == self.current_configuration:
                try:
                    self.current_configuration = self.configurations[x + 1]
                except:
                    self.current_configuration = self.configurations[0]

                break

        return make_response(jsonify({
            "ScreenMessage": ["---", "Changed Configuration:", self.current_configuration["Description"], ""],
            "ScreenDuration": 2,
            "ConfigurationId": self.current_configuration["Id"],
            "ConfigurationDescription": self.current_configuration["Description"]
        }))
