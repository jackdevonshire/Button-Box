from button.default_button import DefaultButton
from user_scripts import UserScripts

class ScriptButton(DefaultButton):
    def __init__(self, event_configuration, display_service, script_service: UserScripts):
        super().__init__(event_configuration, display_service)
        self.script_service = script_service
    def handle(self):
        return self.script_service.call_script(self.event_configuration["Action"])
