from datetime import datetime
import time
from display_service import DisplayService
import multiprocessing

"""
To add a custom script:
1. Copy the __example_script method and rename it to __what_you_want_to_call_it
2. Add this method name to the self.scripts list (again copy the example), the key here (left value) should
   be equal to what you will put inside the button configuration "Action" field.
"""

class UserScripts:
    def __init__(self, display_service: DisplayService):
        self.display_service = display_service
        self.scripts = {
            "flash_time_example": self.show_time_once_example,
            "show_time_example": self.show_time
        }
        self.active_process = None

    def call_script(self, method_name):
        self.stop_current_script()
        self.active_process = multiprocessing.Process(target=self.scripts[method_name], args=())
        self.active_process.start()

    def stop_current_script(self):
        if self.active_process is not None:
            self.active_process.terminate()
            self.active_process = None
    def show_time_once_example(self):
        now = datetime.now()
        time = "%s:%s:%s" % (now.hour, now.minute, now.second)
        self.display_service.display_temporary_message(["", "Current Time", time, ""], 2)

    def show_time(self):
        while True:
            now = datetime.now()
            current_time = "%s:%s:%s" % (now.hour, now.minute, now.second)
            self.display_service.display_permanent(["", "Current Time", current_time, ""])

            time.sleep(1)