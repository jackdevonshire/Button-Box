from concurrent.futures import ThreadPoolExecutor
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload
import datetime
import ipaddress
import traceback
from app import app
from app.core.box_monitor import BoxMonitor
from app.core.events import event_bus
from app.core.models import Configuration, Binding, Setting, IntegrationAction
from app.core.types import HttpStatusCode, NetworkResponse, PhysicalKey, EventType, CONTROLS

CONTROL_LABELS = {control["id"]: control["label"] for control in CONTROLS}
LEARN_SECONDS = 5


def find_matching_bindings(bindings, control, event, states):
    """
    Returns the bindings that should fire for a control event. A binding matches when its control and event match and
    all of its modifiers are currently on. If several match, only the most specific (most modifiers) fire - so a
    binding with a modifier replaces the plain binding while that modifier is held, rather than both running.
    """
    matches = [
        binding for binding in bindings
        if binding.enabled
        and binding.physical_key == control.value
        and binding.event_type == event.value
        and all(states.get(PhysicalKey[modifier]) == EventType.ON for modifier in (binding.modifiers or []))
    ]
    if not matches:
        return []

    most_modifiers = max(len(binding.modifiers or []) for binding in matches)
    return [binding for binding in matches if len(binding.modifiers or []) == most_modifiers]


def describe_event(control, event):
    return f"{CONTROL_LABELS.get(control.name, control.name)} {event.name.lower()}"


class ButtonBoxService:
    def __init__(self, db: SQLAlchemy):
        self.current_configuration = None
        self.current_bindings = []

        self.db = db
        self.__initialised = False
        self.display_service = None
        self.integration_factory = None
        self.states = {}

        # Actions run in the background so the box gets an immediate response and can carry on reading buttons.
        # A single worker keeps actions in the order they were pressed (e.g. key down before key up).
        self.__action_worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="action-worker")
        self.box_ip = ""
        self.monitor = BoxMonitor(get_ip=lambda: self.box_ip, on_box_found=self.__on_box_found,
                                  on_status_change=self.__on_status_change)

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
                self.__load_configuration(Configuration.query.order_by(Configuration.id).first())
                # Now initiate communication with Button Box
                self.reconnect()

            self.monitor.start()
            self.__initialised = True

    # region Connection

    def reconnect(self):
        self.box_ip = Setting.query.filter_by(key="ButtonBoxIP").first().value
        self.display_service.update_host_ip(self.box_ip)
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
            event_bus.log("system", f"Button box found at {ip}")
            self.api_change_ip(ip)

    def __on_box_found(self, ip):
        if ip != self.box_ip:
            event_bus.log("system", f"Button box found at {ip}")
            with app.app_context():
                self.api_change_ip(ip)
        else:
            # Same IP but the box was unreachable - it may have restarted, so resend the screen
            self.display_service.force_default_message()

    def __on_status_change(self, online):
        event_bus.log("system", "Button box online" if online else "Button box offline")
        event_bus.publish("status", self.get_status())

    def get_status(self):
        status = self.monitor.get_status()
        status["ActiveConfiguration"] = self.current_configuration.to_api_response()
        status["States"] = {key.name: event.name for key, event in self.states.items()}
        return status

    # endregion

    # region Configurations

    def __load_configuration(self, configuration):
        self.current_configuration = configuration
        self.current_bindings = Binding.query.options(
            joinedload(Binding.integration_action).joinedload(IntegrationAction.integration)
        ).filter_by(configuration_id=configuration.id).all()
        self.display_service.set_default_message(configuration.get_display_lines())

    def api_change_active_configuration(self, configuration_id):
        new_configuration = Configuration.query.filter_by(id=configuration_id).first()
        if not new_configuration:
            return NetworkResponse().with_error("Configuration does not exist", HttpStatusCode.NotFound)

        changed = self.current_configuration is None or self.current_configuration.id != new_configuration.id
        self.__load_configuration(new_configuration)
        self.display_service.force_default_message()

        if changed:
            event_bus.log("system", f"Switched to {new_configuration.name}")
            event_bus.publish("configuration", {"activeConfigurationId": new_configuration.id})

        return NetworkResponse()

    def refresh_current_configuration(self):
        self.api_change_active_configuration(self.current_configuration.id)

    # endregion

    # region Events and actions

    def api_handle_event(self, switch, event):
        # Convert to our version of the switch and event
        switch = PhysicalKey[switch]
        event = EventType.map_from_on_off(event)

        # Save the state before matching, so a modifier counts as held from the moment it's switched on
        self.states[switch] = event
        event_data = {"control": switch.name, "event": event.name.lower(), "bindings": []}

        if self.training_mode:
            if self.training_mode_activated + datetime.timedelta(seconds=LEARN_SECONDS) > datetime.datetime.now():
                # If still in training mode, log event and then return so it isn't handled
                self.training_event = (switch, event)
                self.training_mode = False
                self.display_service.display_temporary_message(["", "Button Logged", "", ""], 2)
                event_bus.publish("press", event_data)
                event_bus.publish("learned", {"control": switch.name, "event": event.name.lower()})
                return NetworkResponse()
            else:
                self.training_mode = False

        # Now handle the event
        bindings = find_matching_bindings(self.current_bindings, switch, event, self.states)
        for binding in bindings:
            action = binding.integration_action
            self.__action_worker.submit(self.__run_action, action.id, action.integration.id)
            event_data["bindings"].append(binding.id)

        event_bus.publish("press", event_data)
        if bindings:
            names = ", ".join(binding.name or binding.integration_action.name for binding in bindings)
            event_bus.log("press", f"{describe_event(switch, event)} → {names}", control=switch.name,
                          event=event.name.lower())
        elif event == EventType.ON:
            # Only log unmapped presses, not their releases, to keep the log readable
            event_bus.log("press", f"{describe_event(switch, event)} (not mapped)", control=switch.name,
                          event=event.name.lower())

        return NetworkResponse()

    def __run_action(self, action_id, integration_id):
        with app.app_context():
            action_name = f"Action {action_id}"
            try:
                action = self.db.session.get(IntegrationAction, action_id)
                if action is None:
                    return
                action_name = action.name

                integration_service = self.integration_factory.get_integration_by_id(integration_id)
                if not integration_service.is_active:
                    event_bus.log("error", f"{action_name} skipped", detail=f"{integration_service.name} is turned off")
                    return
                integration_service.handle_action(action, self.display_service, self)
            except Exception as e:
                print(traceback.format_exc())
                event_bus.log("error", f"{action_name} failed", detail=f"{type(e).__name__}: {e}")

    def api_test_action(self, action_id):
        action = self.db.session.get(IntegrationAction, action_id)
        if action is None:
            return NetworkResponse().with_error("Action does not exist", HttpStatusCode.NotFound)

        event_bus.log("action", f"Tested {action.name}")
        self.__action_worker.submit(self.__run_action, action.id, action.integration_id)
        return NetworkResponse()

    # endregion

    # region Learn mode - the next button pressed is reported instead of running its actions

    def start_learning(self):
        self.training_mode = True
        self.training_mode_activated = datetime.datetime.now()
        self.training_event = (None, None)
        self.display_service.display_temporary_message(["", "Training Mode", "Press a button", ""], LEARN_SECONDS)

    def get_learned(self):
        """Returns the control learned (if any) and whether learn mode is still waiting for one"""
        control, event = self.training_event
        if control and event:
            self.training_mode = False
            self.training_event = (None, None)
            return {"active": False, "control": control.name, "event": event.name.lower()}

        if self.training_mode_activated + datetime.timedelta(seconds=LEARN_SECONDS) < datetime.datetime.now():
            self.training_mode = False
        return {"active": self.training_mode, "control": None, "event": None}

    # endregion
