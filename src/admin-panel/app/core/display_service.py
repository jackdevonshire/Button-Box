import threading
import requests

LCD_ROWS = 4
LCD_COLS = 20  # The box truncates anything longer than this


class DisplayService:
    """
    Sends messages to the button box LCD. All sends go through a single background worker so requests never
    overlap on the box, and only the most recent pending message is sent - if several messages are queued while
    the box is busy, the stale ones are skipped.
    """

    def __init__(self):
        self.base_url = ""
        self.default_message = []
        self.latest_request = 0

        self.__pending = None
        self.__condition = threading.Condition()
        threading.Thread(target=self.__worker, name="display-worker", daemon=True).start()

    def update_host_ip(self, host_ip):
        host_ip = host_ip.replace("http://", "")
        host_ip = host_ip.replace("/", "")
        self.base_url = "http://" + host_ip + ":8000/display" if host_ip else ""

    def set_default_message(self, default_message):
        self.default_message = default_message

    def display_permanent(self, message, align_center=True):
        self.__send(message)

    def force_default_message(self):
        self.__send(self.default_message)

    def display_temporary_message(self, message, timeout):
        self.latest_request += 1
        current_request = self.latest_request

        if timeout == None:
            return self.display_permanent(message)
        elif timeout == 0:
            return self.display_permanent(self.default_message)

        self.display_permanent(message)
        threading.Timer(timeout, self.__reset_default_message, args=(current_request,)).start()

    def __reset_default_message(self, current_request):
        # Only return default message if this is the most up to date message request
        if current_request == self.latest_request:
            self.force_default_message()

    @staticmethod
    def normalise_message(message):
        lines = [str(line) for line in (message or [])][:LCD_ROWS]
        lines += [""] * (LCD_ROWS - len(lines))
        return [line[:LCD_COLS] for line in lines]

    def __send(self, message):
        with self.__condition:
            self.__pending = self.normalise_message(message)
            self.__condition.notify()

    def __worker(self):
        while True:
            with self.__condition:
                while self.__pending is None:
                    self.__condition.wait()
                message, self.__pending = self.__pending, None

            if not self.base_url:
                continue

            try:
                requests.post(self.base_url, json={"ScreenMessage": message, "AlignCenter": True}, timeout=3)
            except requests.RequestException as e:
                print(f"Display Service - Failed to update display: {e}")
