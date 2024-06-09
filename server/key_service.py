import time

from pynput.keyboard import Controller

from types import NetworkResponse
from user_scripts import UserScripts


class KeyService:
    def __init__(self, configuration):
        self.keyboard = Controller()
        self.user_script_service = UserScripts()
        self.configuration = configuration
        self.current_configuration = configuration[self.configuration[0]]

    def handle_key_event(self, button_reference, event):
        current_button_config = {}
        for button in self.current_configuration["Buttons"]:
            if button["Reference"] == button_reference:
                current_button_config = button
                break

        if len(current_button_config.items()) == 0:
            return NetworkResponse.with_data({
                "ScreenMessage": "\nError\nInvalid Button:\n"+button_reference+"\n",
                "ScreenDuration": 2
            })

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

    def switch_configuration(self):
        # Switch to next configuration
        for x in range(0, len(self.configuration) - 1):
            if self.configuration[x] == self.current_configuration:
                try:
                    self.current_configuration = self.configuration[x + 1]
                except:
                    self.current_configuration = self.configuration[0]

                break

        return NetworkResponse.with_data({
            "ScreenMessage": "---\nChanged Configuration\n" + self.current_configuration["Description"] + "\n---",
            "ScreenDuration": 2,
            "ConfigurationId": self.current_configuration["Id"],
            "ConfigurationDescription": self.current_configuration["Description"]
        })
