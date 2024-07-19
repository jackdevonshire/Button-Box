import time
import requests


class Client():
    def __init__(self, host_ip, auth_token):
        self.base_url = "http://" + host_ip.replace("http://", "").replace("/", "")
        self.auth_token = auth_token

    def handle_event(self, event, button_reference):
        endpoint = self.base_url + "/event"
        requests.post(endpoint, json={
            "AuthenticationToken": self.auth_token,
            "Event": event,
            "ButtonReference": button_reference
        })

    def setup(self):
        endpoint = self.base_url + "/setup"
        requests.post(endpoint, json={
            "AuthenticationToken": self.auth_token
        })

        self.display_service.display_message(["", "Starting Up", "Disable All Switches", ""])
        time.sleep(5)