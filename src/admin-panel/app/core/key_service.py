from flask_sqlalchemy import SQLAlchemy
from app.core.models import Integration, IntegrationAction, Configuration, ConfigurationButton, Setting
from app import app


class KeyService:
    def __init__(self, db: SQLAlchemy):
        self.current_configuration_id = None
        self.db = db
        self.__initialised = False

    def initialise(self):
        if not self.__initialised:
            # Set current config to default config
            with app.app_context():
                first_configuration = Configuration.query.order_by(Configuration.id).first()
                if first_configuration:
                    self.current_configuration_id = first_configuration.id

            self.__initialised = True
