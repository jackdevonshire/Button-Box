from app.integrations.integration import BaseIntegrationService
from app.core.models import IntegrationAction, Configuration, ConfigurationButton
from app.core.display_service import DisplayService
from app.core.button_box_service import ButtonBoxService
from app import db


class ModeSelectionService(BaseIntegrationService):
    def __init__(self):
        super().__init__()
        # Core details - must be present for EVERY integration
        self.id = 2
        self.name = "Mode Selection"
        self.description = "Switch the box to another configuration"
        self.is_active = True
        self.configuration = {}

        self.ui_icon = "layers"
        self.user_actions = False  # One action is generated per configuration

    def initialise_service(self):
        pass

    def describe(self):
        description = super().describe()
        description["note"] = "Creates a “switch to” action for each configuration automatically."
        return description

    def sync_actions(self):
        configurations = {configuration.id: configuration for configuration in Configuration.query.all()}
        actions_by_configuration = {}

        for action in IntegrationAction.query.filter_by(integration_id=self.id).all():
            configuration_id = action.configuration["ConfigurationId"]
            if configuration_id not in configurations or configuration_id in actions_by_configuration:
                # Remove actions (and the buttons using them) for deleted configurations, and any duplicates
                ConfigurationButton.query.filter_by(integration_action_id=action.id).delete()
                db.session.delete(action)
            else:
                actions_by_configuration[configuration_id] = action

        # Ensure every configuration has an action to switch to it, named after the configuration
        for configuration_id, configuration in configurations.items():
            action = actions_by_configuration.get(configuration_id)
            if action is None:
                action = IntegrationAction(integration_id=self.id, configuration={"ConfigurationId": configuration_id})
                db.session.add(action)
            action.name = configuration.name
            action.description = f"Switch current configuration to {configuration.name}"

        db.session.commit()

    def handle_action(self, action: IntegrationAction, display: DisplayService, button_box: ButtonBoxService):
        configuration_id = action.configuration["ConfigurationId"]
        configuration = Configuration.query.filter_by(id=configuration_id).first()

        if configuration:
            button_box.api_change_active_configuration(configuration_id)
