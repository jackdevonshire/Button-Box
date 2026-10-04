from flask import Blueprint

from app.core.types import NetworkResponse
from app.integrations.integration import BaseIntegrationService
from app.core.models import IntegrationAction
from app.core.display_service import DisplayService
from app.core.button_box_service import ButtonBoxService
import subprocess


class CommandService(BaseIntegrationService):
    def __init__(self):
        # Core details - must be present for EVERY integration
        self.id = 3
        self.name = "OS Command"
        self.description = "An integration to run OS commands on windows"
        self.is_active = True  # TODO in future, add an integration manager so we can delete this and just manage on a web page
        self.configuration = {}

        self.url_prefix = "/integration/command"
        self.blueprint = Blueprint('bp_command', __name__, url_prefix=self.url_prefix)
        self.icon = "fas fa-terminal"
    def initialise_service(self):
        pass

    def handle_action(self, action: IntegrationAction, display: DisplayService, button_box: ButtonBoxService):
        display.display_temporary_message(["", action.name, "", ""], 2)

        print("Command Service - Running Command: " + action.configuration)
        # Popen doesn't wait for the command to finish, so e.g. launching an app doesn't hold up other buttons
        # CREATE_NO_WINDOW stops a console flashing up for the shell itself - apps it launches still show normally
        subprocess.Popen(action.configuration, shell=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))

        return NetworkResponse()
