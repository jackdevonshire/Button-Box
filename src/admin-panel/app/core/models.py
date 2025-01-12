from app import db
from sqlalchemy.dialects.sqlite import JSON
from app.core.types import EventType, PhysicalKey
class Configuration(db.Model):
    __tablename__ = 'configuration'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False)

    def to_api_response(self):
        return {
            "Id": self.id,
            "Name": self.name,
            "Description": self.description
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

class ConfigurationButton(db.Model):
    __tablename__ = 'configuration_button'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    configuration_id = db.Column(db.Integer, db.ForeignKey('configuration.id'), nullable=False)
    physical_key = db.Column(db.Integer, nullable=False)
    event_type = db.Column(db.Integer, nullable=False)
    integration_action_id = db.Column(db.Integer, db.ForeignKey('integration_action.id'), nullable=False)

    configuration = db.relationship('Configuration', backref=db.backref('buttons', lazy=True))
    integration_action = db.relationship('IntegrationAction', backref=db.backref('buttons', lazy=True))

    def to_api_response(self):
        event_name = EventType(self.event_type).name
        return {
            "Id": self.id,
            "PhysicalKey": self.physical_key,
            "EventType": event_name,
            "IntegrationAction": self.integration_action.to_api_response()
        }

class Setting(db.Model):
    __tablename__ = 'setting'

    # Define columns for the "settings" table
    key = db.Column(db.String, primary_key=True, nullable=False)
    value = db.Column(db.String, nullable=False)
    visible = db.Column(db.Boolean, nullable=False)