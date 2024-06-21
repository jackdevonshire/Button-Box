import requests
import display_service


class Client():
    def __init__(self, host_ip, auth_token, display : display_service.DisplayService):
        self.display_service = display
        self.base_url = "http://" + host_ip.replace("http://", "").replace("/", "")
        self.auth_token = auth_token

    def handle_event(self, event, button_reference):
        endpoint = self.base_url + "/event"
        response = requests.post(endpoint, json={
            "AuthenticationToken": self.auth_token,
            "Event": event,
            "ButtonReference": button_reference
        })

        self.display_service.display_temporary_message(response.json()["ScreenMessage"], 5, response.json()["DefaultScreenMessage"])

    def setup(self):
        endpoint = self.base_url + "/setup"
        response = requests.post(endpoint, json={
            "AuthenticationToken": self.auth_token
        })

        self.display_service.display_temporary_message(["", "Starting Up", "Disable All Switches", ""], 5, response.json()["DefaultScreenMessage"])