from app import db, app
import json
from flask_sqlalchemy import SQLAlchemy
from app.core.core_service import CoreService
from app.core.models import Integration, IntegrationAction
from app.core.display_service import DisplayService
from app.core.button_box_service import ButtonBoxService

class BaseIntegrationService:
    def __init__(self):
        # Core details
        self.id = None
        self.name = None
        self.description = None
        self.is_active = None  # Default for first run - after that, whether it's active is stored in the database
        self.configuration = None

        # How the web UI presents this integration
        self.ui_icon = "plug"         # Icon name in the web UI's icon set
        self.action_editor = None     # Which editor the UI shows for this integration's actions
        self.user_actions = True      # False when actions are generated automatically and can't be created by hand

        # Other setup
        self.db = None
        self.core_service = None

    """
    This initialises the configuration in the database, so that it is available to be seen in the UI if it is active
    """

    def initialise_database(self, db: SQLAlchemy, core_service: CoreService):
        self.db = db
        self.core_service = core_service

        with app.app_context():
            existing_integration = Integration.query.filter_by(id=self.id).first()
            if existing_integration:
                # The database is the source of truth for whether an integration is turned on
                self.is_active = existing_integration.is_active
                existing_integration.name = self.name
                existing_integration.description = self.description
            else:
                new_integration = Integration(
                    id=self.id,
                    name=self.name,
                    description=self.description,
                    is_active=self.is_active,
                    configuration=json.dumps(self.configuration)
                )

                self.db.session.add(new_integration)
            self.db.session.commit()

    def set_active(self, is_active):
        integration = Integration.query.filter_by(id=self.id).first()
        integration.is_active = is_active
        self.db.session.commit()
        self.is_active = is_active

    def describe(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "active": bool(self.is_active),
            "icon": self.ui_icon,
            "actionEditor": self.action_editor,
            "userActions": self.user_actions,
            "actionCount": IntegrationAction.query.filter_by(integration_id=self.id).count(),
        }

    """
    This initialises anything specific to the service. Unlike the database initialise() method,
    this will be used by each individual service to initialise anything they need to do.

    Such as authenticating with an external API etc etc
    """

    def initialise_service(self):
        pass

    """
    Called whenever data this integration's actions depend on changes (e.g. configurations being added or removed),
    so integrations that generate their actions automatically can keep them up to date.
    """

    def sync_actions(self):
        pass

    """
    Checks an action's configuration is valid for this integration, returning the cleaned-up configuration.
    Raises ValueError with a message for the user when it isn't.
    """

    def validate_action_configuration(self, configuration):
        return configuration

    def handle_action(self, action: IntegrationAction, display: DisplayService, button_box: ButtonBoxService):
        pass
