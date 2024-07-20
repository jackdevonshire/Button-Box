import os
from button.default_button import DefaultButton


class CommandButton(DefaultButton):
    def handle(self):
        os.system(self.event_configuration["Action"])

        if "ScreenMessage" in self.event_configuration and "ScreenDuration" in self.event_configuration:
            return self.display_service.display_temporary_message(self.event_configuration["ScreenMessage"], self.event_configuration["ScreenDuration"])
