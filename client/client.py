import requests
import display_service


class Client():
    def __init__(self, host_ip, auth_token, display : display_service.DisplayService):
        self.display_service = display
        self.base_url = host_ip.replace("/", "")
        self.auth_token = auth_token

    def handle_event(self, event, button_reference):
        endpoint = self.base_url + "/event"
        response = requests.post(endpoint, {
            "AuthenticationToken": self.auth_token,
            "Event": event,
            "ButtonReference": button_reference
        })

        self.display_service.set_temporary_message(response["ScreenMessage"], response["ScreenDuration"])

    def switch_configuration(self):
        endpoint = self.base_url + "/configuration"
        response = requests.post(endpoint, {
            "AuthenticationToken": self.auth_token
        })

        default_message = ["----", "Configuration:", response["ConfigurationDescription"],"----"]
        self.display_service.set_default_message(default_message)
        self.display_service.set_temporary_message(response["ScreenMessage"], response["ScreenDuration"])