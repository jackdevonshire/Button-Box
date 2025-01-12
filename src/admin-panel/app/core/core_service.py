from flask_sqlalchemy import SQLAlchemy
from app.core.models import Integration, IntegrationAction, Configuration, ConfigurationButton, Setting
from app import app


class CoreService:
    def __init__(self, db: SQLAlchemy):
        self.db = db

    def get_dashboard_data(self):
        ip = Setting.query.filter_by(key="ButtonBoxIP").first().value
        active_config_id = Setting.query.filter_by(key="CurrentConfigurationId").first().value
        active_config = Configuration.query.filter_by(id=active_config_id).first()
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
            "All Configurations": [x.to_api_response() for x in all_configurations]
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