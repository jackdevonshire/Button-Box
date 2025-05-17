from flask import Blueprint
from app.integrations.integration import BaseIntegrationService
from app.core.models import IntegrationAction
from app.core.display_service import DisplayService
from app.core.button_box_service import ButtonBoxService
from app.core.types import HttpStatusCode, NetworkResponse


class KeyboardService(BaseIntegrationService):
    def __init__(self):
        # Core details - must be present for EVERY integration
        self.id = 1
        self.name = "Keyboard"
        self.description = "An integration to simulate keyboard interactions on the server hosts machine"
        self.is_active = True  # TODO in future, add an integration manager so we can delete this and just manage on a web page
        self.configuration = {}

        self.url_prefix = "/integration/keyboard"
        self.blueprint = Blueprint('bp_keyboard', __name__, url_prefix=self.url_prefix)

    def initialise_service(self):
        pass

    def handle_action(self, action: IntegrationAction, display: DisplayService, button_box: ButtonBoxService):
        display.display_temporary_message(["HEY THERE"], 2)
        raise NotImplementedError()
