from flask import make_response, jsonify

from button.keybind_button import KeybindButton
from button.method_button import MethodButton
from button.command_button import CommandButton


class KeyService:
    def __init__(self, configurations):
        self.configurations = configurations
        self.current_configuration = self.configurations[0]
        self.initialised_configuration = False
        self.button_states = {}
        self.__initialize_button_states()

    def __initialize_button_states(self):
        for configuration in self.configurations:
            for button in configuration["Buttons"]:
                button_reference = button["Reference"]

                if button_reference not in self.button_states:
                    self.button_states[button_reference] = "OFF"

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
        if event_configuration == None:
            return make_response(jsonify({
                "ScreenMessage": self.current_configuration["DefaultScreenMessage"],
                "ScreenDuration": 1,
                "DefaultScreenMessage": self.current_configuration["DefaultScreenMessage"]
            }))

        self.button_states[button_reference] = event

        if event_configuration["Type"] == "Mode":
            return self.switch_configuration()

        for requirement in event_configuration["Requirements"]:
            req_button_ref = requirement["ButtonReference"]
            req_state = requirement["RequiredState"]

            if self.button_states[req_button_ref] != req_state:
                return make_response(jsonify({
                    "ScreenMessage": requirement["ErrorMessage"],
                    "ScreenDuration": 2,
                    "DefaultScreenMessage": self.current_configuration["DefaultScreenMessage"]
                }))

        if event_configuration["Type"] == "Keybind":
            button = KeybindButton(event_configuration)
        elif event_configuration["Type"] == "Method":
            button = MethodButton(event_configuration)
        elif event_configuration["Type"] == "Command":
            button = CommandButton(event_configuration)

        result = button.handle()
        if result is not None:
            message, duration = result

            return make_response(jsonify({
                "ScreenMessage": message,
                "ScreenDuration": duration,
                "DefaultScreenMessage": self.current_configuration["DefaultScreenMessage"]
            }))

        if "ScreenMessage" in self.current_configuration and "ScreenDuration" in self.current_configuration:
            return make_response(jsonify({
                "ScreenMessage": self.current_configuration["ScreenMessage"],
                "ScreenDuration": self.current_configuration["ScreenDuration"],
                "DefaultScreenMessage": self.current_configuration["DefaultScreenMessage"]
            }))

        return make_response(jsonify({
            "ScreenMessage": ["", "", "", ""],
            "ScreenDuration": 0,
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
            "ScreenMessage": self.current_configuration["DefaultScreenMessage"],
            "ScreenDuration": 0,
            "DefaultScreenMessage": self.current_configuration["DefaultScreenMessage"]
        }))

    def get_default_screen_message(self):
        return self.current_configuration["DefaultScreenMessage"]
