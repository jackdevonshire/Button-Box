from app.integrations.keyboard.controllers import bp_keyboard, url_prefix

from app.integrations.integration import BaseIntegrationService
from app.core.models import IntegrationAction


class KeyboardService(BaseIntegrationService):
    def __init__(self):
        # Core details - must be present for EVERY integration
        self.id = 1
        self.name = "Keyboard"
        self.description = "An integration to simulate keyboard interactions on the server hosts machine"
        self.is_active = True # TODO in future, add an integration manager so we can delete this and just manage on a web page
        self.configuration = {}
        self.blueprint = bp_keyboard
        self.url_prefix = url_prefix

    def initialise_service(self):
        pass

    def handle_action(self, action: IntegrationAction):
        print("HEY, HANDLING ACTION")
        raise NotImplementedError()
