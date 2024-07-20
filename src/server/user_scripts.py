from datetime import datetime
from display_service import DisplayService

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
            "example_script": self.__example_script,
            "show_time_example": self.__show_time_example
        }

    def call_script(self, method_name):
        return self.scripts[method_name]()

    # Example Script
    def __example_script(self):
        print("This is an example script")

    def __show_time_example(self):
        now = datetime.now()
        time = "%s:%s:%s" % (now.hour, now.minute, now.second)

        self.display_service.display_temporary_message(time, 2)