from concurrent.futures import ThreadPoolExecutor
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload
import datetime
import ipaddress
import traceback
from app import app
from app.core.box_monitor import BoxMonitor
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

        # Actions run in the background so the box gets an immediate response and can carry on reading buttons.
        # A single worker keeps actions in the order they were pressed (e.g. key down before key up).
        self.__action_worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="action-worker")
        self.box_ip = ""
        self.monitor = BoxMonitor(get_ip=lambda: self.box_ip, on_box_found=self.__on_box_found)

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

            self.monitor.start()
            self.__initialised = True

    def reconnect(self):
        self.box_ip = Setting.query.filter_by(key="ButtonBoxIP").first().value
        self.display_service.update_host_ip(self.box_ip)
        self.display_service.set_default_message(["", "Current Mode", self.current_configuration.name, ""])
        self.display_service.force_default_message()

    def api_change_ip(self, new_ip):
        ip_setting = Setting.query.filter_by(key="ButtonBoxIP").first()
        ip_setting.value = new_ip.strip()

        self.db.session.commit()
        self.reconnect()

        return NetworkResponse()

    def note_box_address(self, ip):
        """Called with the source address of every event, so the box's IP is learned (and kept up to date) automatically"""
        if not ip or ipaddress.ip_address(ip).is_loopback:
            return  # The box is never on this machine - this is a local test request

        self.monitor.record_event()
        if ip != self.box_ip:
            print(f"Button box seen at new address {ip} - updating saved IP")
            self.api_change_ip(ip)

    def __on_box_found(self, ip):
        if ip != self.box_ip:
            with app.app_context():
                self.api_change_ip(ip)
        else:
            # Same IP but the box was unreachable - it may have restarted, so resend the screen
            self.display_service.force_default_message()

    def api_find_box(self):
        ip = self.monitor.scan(wait=True)
        if not ip:
            return NetworkResponse().with_error("Couldn't find the button box on your network", HttpStatusCode.NotFound)
        return NetworkResponse().with_data({"ButtonBoxIP": ip})

    def api_get_status(self):
        status = self.monitor.get_status()
        status["ActiveConfiguration"] = self.current_configuration.to_api_response()
        status["States"] = {key.name: event.name for key, event in self.states.items()}
        return NetworkResponse().with_data(status)

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
                self.__action_worker.submit(self.__run_action, button.integration_action.id,
                                            button.integration_action.integration.id)
                return NetworkResponse()

        print("Button not mapped")

        return NetworkResponse()

    def __run_action(self, action_id, integration_id):
        with app.app_context():
            try:
                action = self.db.session.get(IntegrationAction, action_id)
                if action is None:
                    print(f"Action {action_id} no longer exists")
                    return
                integration_service = self.integration_factory.get_integration_by_id(integration_id)
                integration_service.handle_action(action, self.display_service, self)
            except Exception:
                print(f"Action {action_id} failed:\n{traceback.format_exc()}")

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