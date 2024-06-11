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
        self.initialised_configuration = False

    def handle_key_event(self, button_reference, event):
        current_button_config = {}
        for button in self.current_configuration["Buttons"]:
            if button["Reference"] == button_reference:
                current_button_config = button
                break

        if len(current_button_config.items()) == 0:
            return make_response(jsonify({
                "ScreenMessage": ["", "Error:", "Invalid Button", button_reference],
                "ScreenDuration": 2,
                "DefaultScreenMessage": self.current_configuration["DefaultScreenMessage"]
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

        elif event_configuration["Type"] == "Mode":
            return self.switch_configuration()

        return make_response(jsonify({
            "ScreenMessage": event_configuration["ScreenMessage"],
            "ScreenDuration": event_configuration["ScreenDuration"],
            "DefaultScreenMessage": self.current_configuration["DefaultScreenMessage"]
        }))

    def switch_configuration(self):
        if self.initialised_configuration:
            # Switch to next configuration
            for x in range(0, len(self.configurations)):
                if self.configurations[x]["Id"] == self.current_configuration["Id"]:
                    try:
                        self.current_configuration = self.configurations[x + 1]
                    except:
                        self.current_configuration = self.configurations[0]

                    break
        else:
            self.initialised_configuration = True

        return make_response(jsonify({
            "ScreenMessage": ["---", "Changed", "Configuration", ""],
            "ScreenDuration": 2,
            "DefaultScreenMessage": self.current_configuration["DefaultScreenMessage"]
        }))

    def get_default_screen_message(self):
        return self.current_configuration["DefaultScreenMessage"]