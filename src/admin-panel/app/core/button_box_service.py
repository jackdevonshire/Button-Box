from flask_sqlalchemy import SQLAlchemy

from app.core.display_service import DisplayService
from app.core.models import Integration, IntegrationAction, Configuration, ConfigurationButton, Setting
from app import app
from app.core.types import HttpStatusCode, NetworkResponse, ErrorMessage, PhysicalKey, EventType


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
                self.reconnect()

            self.__initialised = True

    def reconnect(self):
        ip = Setting.query.filter_by(key="ButtonBoxIP").first().value
        self.display_service.update_host_ip(ip)
        self.display_service.set_default_message(["", "Current Mode", self.current_configuration.name, ""])
        self.display_service.force_default_message()

    def api_change_ip(self, new_ip):
        ip_setting = Setting.query.filter_by(key="ButtonBoxIP").first()
        ip_setting.value = new_ip

        self.db.session.commit()
        self.reconnect()

        return NetworkResponse().get()

