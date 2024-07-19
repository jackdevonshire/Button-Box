import time
import requests
import os
class Client():
    def __init__(self, display_service):
        self.base_url = ""
        self.display_service = display_service

    def handle_event(self, event, button_reference):
        endpoint = self.base_url + "/event"
        requests.post(endpoint, json={
            "Event": event,
            "ButtonReference": button_reference
        })

    def setup(self):
        self.display_service.display_message(["", "Start / Restart", "Desktop Server Now ", ""])
        host_ip_file = os.getcwd() + "/host_ip.txt"
        open(host_ip_file, 'w').close()

        while True:
            time.sleep(1)

            with open(host_ip_file) as f:
                first_line = f.readline()
                if first_line != None and first_line != "":
                    host_ip = first_line.strip()
                    self.display_service.display_message(["", "Obtained Host IP", "Configuring Box", ""])
                    self.base_url = "http://" + host_ip.replace("http://", "").replace("/", "")
                    break