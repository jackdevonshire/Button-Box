import time
import requests
import threading


class DisplayService:
    def __init__(self, host_ip):
        host_ip = host_ip.replace("http://", "")
        host_ip = host_ip.replace("/", "")

        self.base_url = "http://" + host_ip + ":8000/display"
        self.default_message = []
        self.latest_request = 0

    def set_default_message(self, default_message):
        self.default_message = default_message

    def display_permanent(self, message, align_center=True):
        requests.post(self.base_url, json={
            "ScreenMessage": message,
            "AlignCenter": align_center
        })

    def force_default_message(self):
        requests.post(self.base_url, json={
            "ScreenMessage": self.default_message,
            "AlignCenter": True
        })

    def display_temporary_message(self, message, timeout):
        self.latest_request += 1
        current_request = self.latest_request

        if timeout == None:
            return self.display_permanent(message)
        elif timeout == 0:
            return self.display_permanent(self.default_message)

        self.display_permanent(message)
        reset_default_thread = threading.Thread(target=self.__wait_to_reset_default_message,
                                                args=(current_request, timeout))
        reset_default_thread.start()

    def __wait_to_reset_default_message(self, current_request, timeout):
        time.sleep(timeout)

        # Only return default message if this is the most up to date message request
        if current_request == self.latest_request:
            self.force_default_message()
