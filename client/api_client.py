import requests


class ApiClient():
    def __init__(self, host_ip, auth_token):
        self.base_url = host_ip.replace("/", "")
        self.auth_token = auth_token

    def handle_event(self, event, button_reference):
        endpoint = self.base_url + "/event"
        return requests.post(endpoint, {
            "AuthenticationToken": self.auth_token,
            "Event": event,
            "ButtonReference": button_reference
        })

    def switch_configuration(self):
        endpoint = self.base_url + "/configuration"
        return requests.post(endpoint, {
            "AuthenticationToken": self.auth_token
        })