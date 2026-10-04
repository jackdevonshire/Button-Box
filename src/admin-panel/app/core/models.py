from app import db
from sqlalchemy.dialects.sqlite import JSON
from app.core.types import EventType, PhysicalKey, Gesture
import datetime


def default_display_lines(configuration_name):
    return ["", "Current Mode", configuration_name, ""]


class Configuration(db.Model):
    __tablename__ = 'configuration'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False)
    display_lines = db.Column(JSON)  # Custom LCD screen while this configuration is active, None for the default

    def get_display_lines(self):
        return self.display_lines or default_display_lines(self.name)

    def to_api_response(self):
        return {
            "Id": self.id,
            "Name": self.name,
            "Description": self.description
        }

    def to_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "displayLines": self.get_display_lines(),
            "customDisplay": self.display_lines is not None,
        }

class Integration(db.Model):
    __tablename__ = 'integration'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False)
    configuration = db.Column(JSON)

    def to_api_response(self):
        return {
            "Id": self.id,
            "Name": self.name,
            "Description": self.description,
            "Active": self.is_active,
            "Configuration": self.configuration
        }

class IntegrationAction(db.Model):
    __tablename__ = 'integration_action'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    integration_id = db.Column(db.Integer, db.ForeignKey('integration.id'), nullable=False)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    configuration = db.Column(JSON, nullable=False)

    integration = db.relationship('Integration', backref=db.backref('actions', lazy=True))

    def to_api_response(self):
        return {
            "Id": self.id,
            "Name": self.name,
            "Description": self.description,
            "Configuration": self.configuration,
            "Integration": {
                "Id": self.integration.id,
                "Name": self.integration.name,
                "Active": self.integration.is_active
            }
        }

    def to_json(self):
        return {
            "id": self.id,
            "integrationId": self.integration_id,
            "integrationName": self.integration.name,
            "name": self.name,
            "description": self.description or "",
            "configuration": self.configuration,
            "bindingCount": len(self.bindings),
        }

class Binding(db.Model):
    """
    Maps something happening on the box to an action. A binding fires when its control sends its event, while all
    of its modifier controls are switched on / held down. When several bindings match, only the most specific ones
    (most modifiers) run, so holding a modifier gives a button a second "layer" of actions.
    """
    __tablename__ = 'configuration_button'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String)
    configuration_id = db.Column(db.Integer, db.ForeignKey('configuration.id'), nullable=False)
    physical_key = db.Column(db.Integer, nullable=False)
    event_type = db.Column(db.Integer, nullable=False)
    integration_action_id = db.Column(db.Integer, db.ForeignKey('integration_action.id'), nullable=False)
    modifiers = db.Column(JSON, nullable=False, default=list)  # Names of controls that must be on, e.g. ["PROTECTED_1"]
    gesture = db.Column(db.String, nullable=False, default=Gesture.SINGLE.value)
    enabled = db.Column(db.Boolean, nullable=False, default=True)

    configuration = db.relationship('Configuration', backref=db.backref('buttons', lazy=True))
    integration_action = db.relationship('IntegrationAction', backref=db.backref('bindings', lazy=True))

    def to_api_response(self):
        event_name = EventType(self.event_type).name
        button = PhysicalKey(self.physical_key).name

        return {
            "Id": self.id,
            "Name": self.name,
            "PhysicalKey": button,
            "EventType": event_name,
            "IntegrationAction": self.integration_action.to_api_response()
        }

    def to_json(self):
        return {
            "id": self.id,
            "configurationId": self.configuration_id,
            "name": self.name or "",
            "control": PhysicalKey(self.physical_key).name,
            "event": EventType(self.event_type).name.lower(),
            "modifiers": self.modifiers or [],
            "gesture": self.gesture,
            "enabled": self.enabled,
            "action": self.integration_action.to_json(),
        }

# Older code refers to bindings as configuration buttons
ConfigurationButton = Binding

class Setting(db.Model):
    __tablename__ = 'setting'

    # Define columns for the "settings" table
    key = db.Column(db.String, primary_key=True, nullable=False)
    value = db.Column(db.String, nullable=False)
    visible = db.Column(db.Boolean, nullable=False)

class JoystickMapping(db.Model):
    """
    Maps a joystick input (a hat direction or a button) to something to do while the configuration is active:
    move the mouse to look around, hold keys, or run an action.
    """
    __tablename__ = 'joystick_mapping'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    configuration_id = db.Column(db.Integer, db.ForeignKey('configuration.id'), nullable=False)
    name = db.Column(db.String, nullable=False, default="")
    device = db.Column(db.String, nullable=False)       # Vendor:product id, e.g. "044F:0406"
    input_type = db.Column(db.String, nullable=False)   # "hat" or "button"
    input = db.Column(db.String, nullable=False)        # Hat direction (up/down/left/right) or button number
    output_type = db.Column(db.String, nullable=False)  # "mouse", "keys" or "action"
    output = db.Column(JSON, nullable=False)
    enabled = db.Column(db.Boolean, nullable=False, default=True)

    configuration = db.relationship('Configuration', backref=db.backref('joystick_mappings', lazy=True))

    def to_json(self):
        return {
            "id": self.id,
            "configurationId": self.configuration_id,
            "name": self.name or "",
            "device": self.device,
            "inputType": self.input_type,
            "input": self.input,
            "outputType": self.output_type,
            "output": self.output,
            "enabled": self.enabled,
        }

class ActivityEntry(db.Model):
    __tablename__ = 'activity'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now, index=True)
    kind = db.Column(db.String, nullable=False)  # press, action, error, system
    title = db.Column(db.String, nullable=False)
    detail = db.Column(db.String)
    control = db.Column(db.String)
    event = db.Column(db.String)

    def to_json(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "kind": self.kind,
            "title": self.title,
            "detail": self.detail,
            "control": self.control,
            "event": self.event,
        }
