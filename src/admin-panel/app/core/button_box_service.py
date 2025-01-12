from flask_sqlalchemy import SQLAlchemy

from app.core.display_service import DisplayService
from app.core.models import Integration, IntegrationAction, Configuration, ConfigurationButton, Setting
from app import app


class ButtonBoxService:
    def __init__(self, db: SQLAlchemy):
        self.current_configuration = None
        self.db = db
        self.__initialised = False
        self.display_service = DisplayService()

    def initialise(self):
        if not self.__initialised:
            # Set current config to default config
            with app.app_context():
                self.current_configuration = Configuration.query.order_by(Configuration.id).first()

                # Now initiate communication with Button Box
                ip = Setting.query.filter_by(key="ButtonBoxIP").first().value
                self.display_service.update_host_ip(ip)
                self.display_service.set_default_message(["", "Current Mode", self.current_configuration.name, ""])

                self.__initialised = True
