from app.core.types import NetworkResponse
from app.integrations.integration import BaseIntegrationService
from app.core.models import IntegrationAction
from app.core.display_service import DisplayService
from app.core.button_box_service import ButtonBoxService
from app.core.events import event_bus
import os
import threading
import traceback


class ScriptService(BaseIntegrationService):
    def __init__(self):
        super().__init__()
        # Core details - must be present for EVERY integration
        self.id = 4
        self.name = "Python Script"
        self.description = "Run Python code on this PC"
        self.is_active = True
        self.configuration = {}

        self.ui_icon = "code"
        self.action_editor = "script"

    def initialise_service(self):
        pass

    def validate_action_configuration(self, configuration):
        if not isinstance(configuration, str) or not configuration.strip():
            raise ValueError("Enter a script to run")
        try:
            compile(configuration, "<script>", "exec")
        except SyntaxError as e:
            raise ValueError(f"Syntax error on line {e.lineno}: {e.msg}")
        return configuration

    def handle_action(self, action: IntegrationAction, display: DisplayService, button_box: ButtonBoxService):
        display.display_temporary_message(["", action.name, "", ""], 2)

        print("Script Service - Running Python: " + action.configuration)
        # Scripts get their own thread so a long-running one doesn't hold up other buttons. They run in a single
        # namespace (so functions they define can see each other) with this module's globals plus the action context.
        namespace = dict(globals())
        namespace.update(action=action, display=display, button_box=button_box)
        threading.Thread(target=self.__run_script, args=(action.name, action.configuration, namespace),
                         name=f"script-{action.id}", daemon=True).start()

        return NetworkResponse()

    @staticmethod
    def __run_script(name, script, namespace):
        try:
            exec(script, namespace)
        except Exception as e:
            print(traceback.format_exc())
            event_bus.log("error", f"Script failed: {name}", detail=f"{type(e).__name__}: {e}")
