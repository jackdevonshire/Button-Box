from button.default_button import DefaultButton
import pydirectinput
import time


class KeybindButton(DefaultButton):
    def handle(self):
        actions = self.event_configuration["Action"].split(",")
        duration = self.event_configuration["ActionDuration"]

        if duration == 0:
            for action in actions:
                pydirectinput.keyUp(action)

        elif duration == None:
            for action in actions:
                pydirectinput.keyDown(action)
        else:
            for action in actions:
                pydirectinput.keyDown(action)

            time.sleep(duration)
            for action in actions:
                pydirectinput.keyUp(action)

        if "ScreenMessage" in self.event_configuration and "ScreenDuration" in self.event_configuration:
            return self.display_service.display_temporary_message(self.event_configuration["ScreenMessage"], self.event_configuration["ScreenDuration"])