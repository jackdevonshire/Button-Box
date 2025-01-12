from app.integrations.keyboard.controllers import bp_keyboard, url_prefix

from app.integrations.integration import BaseIntegrationService
from app.core.models import IntegrationAction


class KeyboardService(BaseIntegrationService):
    def __init__(self):
        # Core details - must be present for EVERY integration
        self.id = 1
        self.name = "Keyboard"
        self.description = "An integration to simulate keyboard interactions on the server hosts machine"
        self.is_active = True
        self.configuration = {}
        self.blueprint = bp_keyboard
        self.url_prefix = url_prefix

    def handle_action(self, action: IntegrationAction):
        print("HEY, HANDLING ACTION")
        raise NotImplementedError()
