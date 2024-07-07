import os
from button.default_button import DefaultButton


class CommandButton(DefaultButton):
    def handle(self):
        os.system(self.event_configuration["Action"])

        return None
