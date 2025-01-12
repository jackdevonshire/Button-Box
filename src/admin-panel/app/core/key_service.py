from flask_sqlalchemy import SQLAlchemy
from app.core.models import Integration, IntegrationAction, Configuration, ConfigurationButton, Setting
from app import app


class KeyService:
    def __init__(self, db: SQLAlchemy):
        self.db = db

        # Set current config to default config
        with app.app_context():
            first_configuration = Configuration.query.order_by(Configuration.id).first()
            if not first_configuration:
                self.current_configuration_id = None
            else:
                self.current_configuration_id = first_configuration.id
