import time

import requests

class DisplayService:
    def __init__(self, host_ip):
        host_ip = host_ip.replace("http://", "")
        host_ip = host_ip.replace("/","")

        self.base_url = "http://" + host_ip + ":8000/display"
        self.default_message = []

    def set_default_message(self, default_message):
        self.default_message = default_message

    def display_permanent(self, message):
        requests.post(self.base_url, json={
            "ScreenMessage": message
        })

    def force_default_message(self):
        requests.post(self.base_url, json={
            "ScreenMessage": self.default_message
        })

    def display_temporary_message(self, message, timeout):
        if timeout == None:
            return self.display_permanent(message)
        elif timeout == 0:
            return self.display_permanent(self.default_message)

        requests.post(self.base_url, json={
            "ScreenMessage": message
        })

        time.sleep(timeout)

        requests.post(self.base_url, json={
            "ScreenMessage": self.default_message
        })