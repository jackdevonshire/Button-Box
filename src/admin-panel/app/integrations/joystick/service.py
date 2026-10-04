from app import app, db
from app.core.events import event_bus
from app.core.models import IntegrationAction, JoystickMapping
from app.integrations.integration import BaseIntegrationService
from app.joystick.engine import JoystickEngine

HAT_LABELS = {"up": "Hat up", "down": "Hat down", "left": "Hat left", "right": "Hat right"}


def input_label(mapping):
    if mapping["inputType"] == "hat":
        return HAT_LABELS.get(mapping["input"], f"Hat {mapping['input']}")
    return f"Button {mapping['input']}"


class JoystickService(BaseIntegrationService):
    """
    Lets a joystick plugged into this PC do things, like Joystick Gremlin: hat directions and buttons can move the
    mouse to look around, hold keys, or run actions. Mappings belong to a configuration and only apply while it's
    active. Unlike other integrations it has no actions of its own - it's another input, alongside the box.
    """

    def __init__(self):
        super().__init__()
        # Core details - must be present for EVERY integration
        self.id = 5
        self.name = "Joystick"
        self.description = "Use a joystick's hat and buttons to look around, hold keys or run actions"
        self.is_active = True
        self.configuration = {}

        self.ui_icon = "gamepad"
        self.user_actions = False

        self.engine = None
        self.button_box_service = None

    def initialise_service(self):
        self.button_box_service = self.core_service.button_box_service
        self.engine = JoystickEngine(event_bus, is_enabled=lambda: bool(self.is_active), run_action=self.__run_action)
        self.button_box_service.configuration_listeners.append(self.__load_mappings)
        self.engine.start()

    def set_active(self, is_active):
        super().set_active(is_active)
        if not is_active:
            self.engine.stop_outputs()

    def describe(self):
        description = super().describe()
        count = JoystickMapping.query.count()
        description["actionCount"] = count
        description["note"] = (f"{count} {'mapping' if count == 1 else 'mappings'} across your configurations. "
                               "Set them up from the Joystick tab on the panel.")
        return description

    def __load_mappings(self, configuration):
        mappings = JoystickMapping.query.filter_by(configuration_id=configuration.id).all()
        self.engine.set_mappings([mapping.to_json() for mapping in mappings])

    def __run_action(self, action_id, mapping):
        with app.app_context():
            action = db.session.get(IntegrationAction, action_id)
            name = mapping["name"] or (action.name if action else f"Action {action_id}")
        event_bus.log("press", f"Joystick {input_label(mapping).lower()} → {name}")
        self.button_box_service.queue_action(action_id)
