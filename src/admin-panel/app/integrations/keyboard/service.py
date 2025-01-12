from app.integrations.keyboard.controllers import bp_keyboard as bp_keyboard
from app.integrations.integration import BaseIntegrationService


class KeyboardService(BaseIntegrationService):
    def __init__(self):
        # Core details
        self.id = 1
        self.name = "Keyboard"
        self.description = "An integration to simulate keyboard interactions on the server hosts machine"
        self.is_active = True
        self.configuration = {}
        self.blueprint = bp_keyboard