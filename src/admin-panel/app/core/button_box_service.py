from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload
import datetime
from app import app
from app.core.models import Configuration, ConfigurationButton, Setting, IntegrationAction
from app.core.types import HttpStatusCode, NetworkResponse, PhysicalKey, EventType


class ButtonBoxService:
    def __init__(self, db: SQLAlchemy):
        self.current_configuration = None
        self.current_buttons = []

        self.db = db
        self.__initialised = False
        self.display_service = None
        self.integration_factory = None
        self.states = {}

        self.training_mode = False
        self.training_mode_activated = datetime.datetime.now()
        self.training_event = (None, None) # Button, State

    def initialise(self):
        if not self.__initialised:
            from app import display_service, integration_factory
            self.display_service = display_service
            self.integration_factory = integration_factory

            # Set current config to default config
            with app.app_context():
                self.current_configuration = Configuration.query.order_by(Configuration.id).first()
                self.current_buttons = ConfigurationButton.query.options(
                    joinedload(ConfigurationButton.integration_action).joinedload(IntegrationAction.integration)
                ).filter_by(configuration_id=self.current_configuration.id).all()
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

        return NetworkResponse()

    def api_change_active_configuration(self, configuration_id):
        new_configuration = Configuration.query.filter_by(id=configuration_id).first()
        if not new_configuration:
            return NetworkResponse().with_error("Configuration does not exist", HttpStatusCode.NotFound)

        self.current_configuration = new_configuration
        self.current_buttons = ConfigurationButton.query.options(
            joinedload(ConfigurationButton.integration_action).joinedload(IntegrationAction.integration)
        ).filter_by(configuration_id=self.current_configuration.id).all()
        self.display_service.set_default_message(["", "Current Mode", self.current_configuration.name, ""])
        self.display_service.force_default_message()

        return NetworkResponse()

    def api_handle_event(self, switch, event):
        # Convert to our version of the switch and event
        switch = PhysicalKey[switch]
        event = EventType.map_from_on_off(event)

        # Log the event and save the state
        print(f"Event Logged: {switch} - {event}")
        self.states[switch] = event

        if self.training_mode:
            if self.training_mode_activated + datetime.timedelta(seconds=5) > datetime.datetime.now():
                # If still in training mode, log event and then return so it isn't handled
                self.training_event = (switch, event)
                self.training_mode = False
                self.display_service.display_temporary_message(["", "Button Logged", "", ""], 2)
                return NetworkResponse()
            else:
                self.training_mode = False

        # Now handle the event
        for button in self.current_buttons:
            if button.physical_key == switch.value and button.event_type == event.value:
                integration_service = self.integration_factory.get_integration_by_id(button.integration_action.integration.id)
                integration_service.handle_action(button.integration_action, self.display_service, self)
                return NetworkResponse()

        print("Button not mapped")

        return NetworkResponse()

    def refresh_current_configuration(self):
        self.api_change_active_configuration(self.current_configuration.id)

    def api_start_training_mode(self):
        self.training_mode = True
        self.training_mode_activated = datetime.datetime.now()
        self.training_event = (None, None)
        self.display_service.display_temporary_message(["", "Training Mode", "Press a button", ""], 5)
        return NetworkResponse()

    def api_get_trained_event(self):
        physical_key = self.training_event[0]
        event = self.training_event[1]

        if physical_key and event:
            self.training_mode = False
            self.training_event = (None, None)
            return NetworkResponse().with_data({
                "TrainingModeActive": False,
                "PhysicalKey": physical_key.value,
                "EventType": event.value
            })

        # Check if training mode expired
        if self.training_mode_activated + datetime.timedelta(seconds=5) < datetime.datetime.now():
            self.training_mode = False
            return NetworkResponse().with_data({
                "TrainingModeActive": False,
                "PhysicalKey": None,
                "EventType": None
            })

        return NetworkResponse().with_data({
            "TrainingModeActive": True,
            "PhysicalKey": None,
            "EventType": None
        })