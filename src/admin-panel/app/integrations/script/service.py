from flask import Blueprint

from app.core.types import NetworkResponse
from app.integrations.integration import BaseIntegrationService
from app.core.models import IntegrationAction
from app.core.display_service import DisplayService
from app.core.button_box_service import ButtonBoxService
import os


class ScriptService(BaseIntegrationService):
    def __init__(self):
        # Core details - must be present for EVERY integration
        self.id = 4
        self.name = "Python Script"
        self.description = "An integration to run Python scripts"
        self.is_active = True  # TODO in future, add an integration manager so we can delete this and just manage on a web page
        self.configuration = {}

        self.url_prefix = "/integration/script"
        self.blueprint = Blueprint('bp_script', __name__, url_prefix=self.url_prefix)
        self.icon = "fas fa-python"

    def initialise_service(self):
        pass

    def handle_action(self, action: IntegrationAction, display: DisplayService, button_box: ButtonBoxService):
        display.display_temporary_message(["", action.name, "", ""], 2)

        print("Script Service - Running Python: " + action.configuration)
        exec(action.configuration)

        return NetworkResponse()
