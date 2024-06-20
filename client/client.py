import time

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

        if response.json()["ScreenDuration"] is None: # Do not switch back to default message until instructed if duration not set
            return

        time.sleep(response.json()["ScreenDuration"])
        self.display_service.display_message(response.json()["DefaultScreenMessage"])

    def setup(self):
        endpoint = self.base_url + "/setup"
        response = requests.post(endpoint, json={
            "AuthenticationToken": self.auth_token
        })

        self.display_service.display_message(["", "Starting Up", "Disable All Switches", ""])
        time.sleep(5)
        self.display_service.display_message(response.json()["DefaultScreenMessage"])