from button.default_button import DefaultButton
from game_services.ms_flight_sim import MicrosoftFlightSimulator

class MSFlightSimButton(DefaultButton):
    def __init__(self, event_configuration, display_service, msfs_service: MicrosoftFlightSimulator):
        super().__init__(event_configuration, display_service)
        self.msfs_service = msfs_service
    def handle(self):
        return self.msfs_service.handle(self.event_configuration["Action"])
