# Import integration services
from app.integrations.keyboard.controllers import keyboard_service
from app.integrations.mode_selection.controllers import mode_selection_service
from app.integrations.command.controllers import command_service

# List all integrations here
ALL_INTEGRATIONS = [
    keyboard_service,
    mode_selection_service,
    command_service
]


class IntegrationFactory:
    def __init__(self):
        self.integrations_by_id = {}
        for integration in ALL_INTEGRATIONS:
            self.integrations_by_id[integration.id] = integration

    @staticmethod
    def get_all_integrations():
        return ALL_INTEGRATIONS

    def get_integration_by_id(self, id):
        return self.integrations_by_id[id]
