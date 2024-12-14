from button.default_button import DefaultButton

# Original https://github.com/fishbigger/TapoP100
# Copied from https://github.com/almottier/TapoP100
from integrations.PyP100 import PyP100
class TapoButton(DefaultButton):
    def __init__(self, event_configuration, display_service, tapo_integration):

        super().__init__(event_configuration, display_service)
        self.__tapo_integration = tapo_integration
        self.email = tapo_integration["TapoAppEmail"]
        self.password = tapo_integration["TapoAppPassword"]

    def handle(self):
        action_configuration = self.event_configuration["Action"]
        device_type = action_configuration["DeviceType"]
        device_ip = action_configuration["DeviceIP"]
        action = action_configuration["Action"]

        if device_type == "plug":
            return self.handle_plug(device_ip, action)

        return self.display_service.display_temporary_message(["", "Tapo", "Device Type Unknown", ""], 2)

    def handle_plug(self, device_ip, action):
        plug = PyP100.P100(device_ip, self.email, self.password)
        plug.handshake()
        plug.login()

        if action == "on":
            plug.turnOn()
            return self.display_service.display_temporary_message(["", "Tapo Plug", "Turned On", ""], 2)

        elif action == "off":
            plug.turnOff()
            return self.display_service.display_temporary_message(["", "Tapo Plug", "Turned Off", ""], 2)

        elif action == "get_status":
            info = plug.getDeviceInfo()
            device_on = info["device_on"]

            if device_on:
                status = "On"
            else:
                status = "Off"

            return self.display_service.display_temporary_message(["", "Tapo Plug", f"Currently {status}", ""], 2)

        return self.display_service.display_temporary_message(["", "Whoops", "An error occurred", ""], 2)