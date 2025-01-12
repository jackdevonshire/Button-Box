from flask_sqlalchemy import SQLAlchemy

from app.core.display_service import DisplayService
from app.core.models import Integration, IntegrationAction, Configuration, ConfigurationButton, Setting
from app import app
from app.core.types import HttpStatusCode, NetworkResponse, ErrorMessage, PhysicalKey, EventType
from app.integrations.integration_factory import integration_factory
from sqlalchemy.orm import joinedload

class ButtonBoxService:
    def __init__(self, db: SQLAlchemy):
        self.current_configuration = None
        self.current_buttons = []

        self.db = db
        self.__initialised = False
        self.display_service = DisplayService()
        self.states = {}

    def initialise(self):
        if not self.__initialised:
            # Set current config to default config
            with app.app_context():
                self.current_configuration = Configuration.query.order_by(Configuration.id).first()
                self.current_buttons = ConfigurationButton.query.options(
                    joinedload(ConfigurationButton.integration_action)) \
                    .filter_by(configuration_id=self.current_configuration.id).all()
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

    def api_change_active_configuration(self, configuration_id):
        new_configuration = Configuration.query.filter_by(id=configuration_id).first()
        if not new_configuration:
            return NetworkResponse().with_error("Configuration does not exist", HttpStatusCode.NotFound)

        self.current_configuration = new_configuration
        self.current_buttons = self.current_buttons = ConfigurationButton.query.options(joinedload(ConfigurationButton.integration_action)).filter_by(configuration_id=self.current_configuration.id).all()
        self.display_service.set_default_message(["", "Current Mode", self.current_configuration.name, ""])
        self.display_service.force_default_message()
        return NetworkResponse().get()

    def api_handle_event(self, switch, event):
        # Convert to our version of the switch and event
        switch = PhysicalKey[switch]
        event = EventType.map_from_on_off(event)

        # Log the event and save the state
        print(f"Event Logged: {switch} - {event}")
        self.states[switch] = event

        # Now handle the event
        for button in self.current_buttons:
            if button.physical_key == switch.value and button.event_type == event.value:
                integration_service = integration_factory.get_integration_by_id(button.integration_action_id)
                integration_service.handle_action(button.integration_action, self.display_service)
                return NetworkResponse().get()

        self.display_service.display_temporary_message(["", "Button Not", "Mapped", ""], 1)

        return NetworkResponse().get()