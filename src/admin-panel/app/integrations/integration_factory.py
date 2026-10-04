# Import integration services
from app.integrations.keyboard.service import KeyboardService
from app.integrations.mode_selection.service import ModeSelectionService
from app.integrations.command.service import CommandService
from app.integrations.script.service import ScriptService

# List all integrations here
ALL_INTEGRATIONS = [
    KeyboardService(),
    ModeSelectionService(),
    CommandService(),
    ScriptService(),
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
