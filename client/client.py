import requests
import display_service


class Client():
    def __init__(self, host_ip, auth_token, display : display_service.DisplayService):
        self.display_service = display
        self.base_url = "http://" + host_ip.replace("http://", "").replace("/", "")
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

        self.display_service.set_default_message(response["DefaultScreenMessage"])
        self.display_service.set_temporary_message(response["ScreenMessage"], response["ScreenDuration"])