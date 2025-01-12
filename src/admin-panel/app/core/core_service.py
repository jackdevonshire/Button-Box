from flask_sqlalchemy import SQLAlchemy
from app.core.models import Integration, IntegrationAction, Configuration, ConfigurationButton, Setting
from app.integrations.integration_factory import IntegrationFactory
from app.core.types import HttpStatusCode, NetworkResponse, ErrorMessage, PhysicalKey, EventType

class CoreService:
    def __init__(self, db: SQLAlchemy, key_service):
        self.db = db
        self.key_service = key_service

    def get_nav_links(self):
        nav_links = {}
        for integration in IntegrationFactory().get_all_integrations():
            if integration.is_active:
                nav_links[integration.name] = integration.url_prefix
        return nav_links

    def get_dashboard_data(self):
        ip = Setting.query.filter_by(key="ButtonBoxIP").first().value
        active_config = Configuration.query.filter_by(id=self.key_service.current_configuration_id).first()
        all_configurations = Configuration.query.all()

        if ip == "":
            ip = "Please enter Button Box IP"

        if len(all_configurations) <= 0:
            return {
                "ButtonBoxIP": ip,
                "ActiveConfiguration": {
                    "Id": -1,
                    "Name": "",
                    "Description": ""
                },
                "All Configurations": []
            }

        return {
            "ButtonBoxIP": ip,
            "ActiveConfiguration": {
                "Id": active_config.id,
                "Name": active_config.name,
                "Description": active_config.description
            },
            "AllConfigurations": [x.to_api_response() for x in all_configurations]
        }

    def get_configuration_data(self, id):
        configuration = Configuration.query.filter_by(id=id).first()
        configuration_buttons = ConfigurationButton.query.filter_by(configuration_id=id).all()
        all_integration_actions = IntegrationAction.query.all()
        all_integration_actions = [x.to_api_response() for x in all_integration_actions]

        available_integration_actions = [] # Filter by only active integrations
        for action in all_integration_actions:
            if action["Integration"]["Active"]:
                available_integration_actions.append(action)

        return {
            "Id": configuration.id,
            "Name": configuration.name,
            "Description": configuration.description,
            "Buttons": [x.to_api_response() for x in configuration_buttons],
            "AvailableActions": available_integration_actions,
            "AvailableButtons": PhysicalKey.to_dict()
        }

    def api_create_configuration(self, name, description):
        new_configuration = Configuration(name=name, description=description)
        self.db.session.add(new_configuration)
        self.db.session.commit()
        return NetworkResponse().get()

    def api_remove_configuration(self, id):
        configuration = Configuration.query.filter_by(id=id).first()
        if not configuration:
            return

        configuration_buttons = ConfigurationButton.query.filter_by(configuration_id=id).all()
        if len(configuration_buttons) > 0:
            return NetworkResponse().with_error("Please delete the buttons in this configuration before removing it", HttpStatusCode.BadRequest).get()

        self.db.session.delete(configuration)
        self.db.session.commit()
        return NetworkResponse().get()

    def api_create_button(self, configuration_id, physical_button, event_type, integration_action_id):
        button = ConfigurationButton(configuration_id=configuration_id, physical_key=physical_button, event_type=event_type, integration_action_id=integration_action_id)
        self.db.session.add(button)
        self.db.session.commit()
        return NetworkResponse().get()


"""
Dashboard:
    View current active configuration name, description
    View current state of buttons
    
    Change button box IP address - should also change this in display service and trigger a new API call to the box
    Change active configuration

Configuration:
    View all configurations - with active one highlighted
    
    Change default configuration
    Add new configuration
    Edit configuration
    Delete configuration
    
    Add button event to configuration
    Remove button event from configuration
    
Integration:
    Based on individual integrations

"""
