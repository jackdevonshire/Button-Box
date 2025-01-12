from flask_sqlalchemy import SQLAlchemy
from app.core.models import Integration, IntegrationAction, Configuration, ConfigurationButton, Setting
from app import app


class CoreService:
    def __init__(self, db: SQLAlchemy):
        self.db = db


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