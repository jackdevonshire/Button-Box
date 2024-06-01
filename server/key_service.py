from pynput.keyboard import Key, Controller
from types import HttpStatusCode, NetworkResponse


class KeyService:
    def __init__(self, configuration):
        self.keyboard = Controller()
        self.configuration = configuration
        self.current_configuration = configuration["Configurations"][0]

    def handle_key_event(self, button_reference, event):
        pass

    def get_current_configuration(self):
        return NetworkResponse.with_data(
            {
                "Id": self.current_configuration["Id"],
                "Description": self.current_configuration["Description"]
             }).get()

    def get_all_configurations(self):
        configurations = []
        for configuration in self.configuration:
            configurations.append({
                "Id": configuration["Id"],
                "Description": configurations["Description"]
            })

        return NetworkResponse.with_data({
            "Configurations": configurations
        }).get()

    def set_configuration(self, configuration_id):
        switched = False
        for configuration in self.configuration:
            if (configuration["Id"] == configuration_id):
                self.current_configuration = configuration
                switched = True
                break

        if not switched:
            return NetworkResponse.with_error("Invalid Configuration Id").with_status_code(
                HttpStatusCode.BadRequest).get()
