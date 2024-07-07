from button.default_button import DefaultButton
from user_scripts import UserScripts


class MethodButton(DefaultButton):
    def handle(self):
        script_service = UserScripts()
        return script_service.call_script(self.event_configuration["Action"])
