from app.integrations.integration import BaseIntegrationService
from app.core.models import IntegrationAction, Configuration, ConfigurationButton
from app.core.display_service import DisplayService
from app.core.button_box_service import ButtonBoxService
from app import db


class ModeSelectionService(BaseIntegrationService):
    def __init__(self):
        # Core details - must be present for EVERY integration
        self.id = 2
        self.name = "Mode Selection"
        self.description = "An integration to switch between different configurations on the Button Box"
        self.is_active = True
        self.configuration = {}
        self.blueprint = None
        self.url_prefix = None

    def initialise_service(self):
        pass

    def get_actions(self):
        all_available_configurations = Configuration.query.all()
        all_available_configuration_ids = [x.id for x in all_available_configurations]
        current_integration_actions = IntegrationAction.query.filter_by(integration_id=self.id).all()

        # Delete buttons that map to any deleted configurations
        for integration_action in current_integration_actions:
            action_config_id = integration_action.configuration["ConfigurationId"]
            if action_config_id not in all_available_configuration_ids:
                ConfigurationButton.query.filter_by(integration_action_id=integration_action.id).delete()
                IntegrationAction.query.filter_by(id=integration_action.id).delete()
                db.session.commit()

        # Ensure we have an integration action available for all current configurations
        for configuration in all_available_configurations:
            if configuration.id not in [x.configuration["ConfigurationId"] for x in current_integration_actions]:
                new_integration_action = IntegrationAction(integration_id=self.id,
                                                           name=configuration.name,
                                                           description=f"Switch current configuration to {configuration.name}",
                                                           configuration={
                                                               "ConfigurationId": configuration.id
                                                           })
                db.session.add(new_integration_action)
                db.session.commit()

        return IntegrationAction.query.filter_by(integration_id=self.id).all()

    def handle_action(self, action: IntegrationAction, display: DisplayService, button_box: ButtonBoxService):
        configuration_id = action.configuration["ConfigurationId"]
        configuration = Configuration.query.filter_by(id=configuration_id).first()

        if configuration:
            button_box.api_change_active_configuration(configuration_id)
