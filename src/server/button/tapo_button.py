from button.default_button import DefaultButton

class TapoButton(DefaultButton):
    def __init__(self, event_configuration, display_service, tapo_integration):

        super().__init__(event_configuration, display_service)
        self.__tapo_integration = tapo_integration
        self.email = tapo_integration["TapoAppEmail"]
        self.password = tapo_integration["TapoAppPassword"]

    def handle(self):
        print(self.email)
        print(self.password)
        return self.display_service.display_temporary_message(["", "Testing", "", ""], 2)
