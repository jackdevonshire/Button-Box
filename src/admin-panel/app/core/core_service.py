from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload

from app.core.models import Configuration, ConfigurationButton, Setting, IntegrationAction
from app.core.types import HttpStatusCode, NetworkResponse, PhysicalKey


class CoreService:
    def __init__(self, db: SQLAlchemy, button_box_service, integration_factory):
        self.db = db
        self.button_box_service = button_box_service
        self.integration_factory = integration_factory

    def get_nav_links(self):
        nav_links = {}
        for integration in self.integration_factory.get_all_integrations():
            if integration.is_active and integration.blueprint is not None and integration.url_prefix is not None:
                nav_links[integration.name] = integration.url_prefix
        return nav_links

    def get_dashboard_data(self):
        ip = Setting.query.filter_by(key="ButtonBoxIP").first().value
        active_config = self.button_box_service.current_configuration
        all_configurations = Configuration.query.all()

        if ip == "":
            ip = "Enter IP Here"

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
        configuration_buttons = ConfigurationButton.query.options(
            joinedload(ConfigurationButton.integration_action).joinedload(IntegrationAction.integration)
        ).filter_by(configuration_id=id).all()

        all_integration_actions = []
        for integration in self.integration_factory.get_all_integrations():
            for action in integration.get_actions():
                all_integration_actions.append(action.to_api_response())

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
        self.button_box_service.refresh_current_configuration()
        return NetworkResponse().get()

    def api_remove_configuration(self, id):
        configuration = Configuration.query.filter_by(id=id).first()
        if not configuration:
            return

        if self.button_box_service.current_configuration.id == configuration.id:
            return NetworkResponse().with_error("You cannot delete an active configuration", HttpStatusCode.BadRequest).get()

        all_configurations = len(Configuration.query.all())
        if all_configurations <= 1:
            return NetworkResponse().with_error("You must always have at-least one configuration present", HttpStatusCode.BadRequest).get()

        configuration_buttons = ConfigurationButton.query.filter_by(configuration_id=id).all()
        if len(configuration_buttons) > 0:
            return NetworkResponse().with_error("Please delete the buttons in this configuration before removing it", HttpStatusCode.BadRequest).get()

        self.db.session.delete(configuration)
        self.db.session.commit()
        self.button_box_service.refresh_current_configuration()
        return NetworkResponse().get()

    def api_create_button(self, configuration_id, button_name, physical_button, event_type, integration_action_id):
        button = ConfigurationButton(configuration_id=configuration_id, name=button_name, physical_key=physical_button, event_type=event_type, integration_action_id=integration_action_id)
        self.db.session.add(button)
        self.db.session.commit()
        self.button_box_service.refresh_current_configuration()
        return NetworkResponse().get()

    def api_remove_button(self, id):
        button = ConfigurationButton.query.filter_by(id=id).first()
        if not button:
            return

        self.db.session.delete(button)
        self.db.session.commit()
        self.button_box_service.refresh_current_configuration()
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
