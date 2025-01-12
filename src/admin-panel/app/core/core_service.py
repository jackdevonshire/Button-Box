from flask_sqlalchemy import SQLAlchemy
from app.core.models import Integration, IntegrationAction, Configuration, ConfigurationButton, Setting
from app.integrations.integration_factory import IntegrationFactory


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
