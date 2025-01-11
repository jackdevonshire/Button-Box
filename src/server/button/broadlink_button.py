import base64

from button.default_button import DefaultButton
from integrations.Broadlink import broadlink
class BroadlinkButton(DefaultButton):
    def __init__(self, event_configuration, display_service, broadlink_integration):

        super().__init__(event_configuration, display_service)
        self.__broadlink_integration = broadlink_integration

        ip = broadlink_integration["DeviceIP"]
        self.device = broadlink.hello(ip)
        self.device.auth()

    def handle(self):
        action_configuration = self.event_configuration["Action"]
        signal_type = action_configuration["SignalType"].upper()
        description = action_configuration["Description"]
        command = action_configuration["Command"]

        if signal_type == "IR":
            return self.handle_ir_signal(description, command)

        return self.display_service.display_temporary_message(["", "Broadlink", "Signal Type Unknown", ""], 2)

    def handle_ir_signal(self, description, command):
        decoded_command = base64.b64decode(command)
        self.device.send_data(decoded_command)

        return self.display_service.display_temporary_message(["", "Sent RF Signal", description, ""], 2)