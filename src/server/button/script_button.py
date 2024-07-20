from button.default_button import DefaultButton
from user_scripts import UserScripts

class ScriptButton(DefaultButton):
    def __init__(self):
        self.script_Service = UserScripts(self.display_service)
    def handle(self):
        return self.script_Service.call_script(self.event_configuration["Action"])
