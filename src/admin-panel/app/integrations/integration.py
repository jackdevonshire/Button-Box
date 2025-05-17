from app import db, app
import json
from flask_sqlalchemy import SQLAlchemy
from app.core.core_service import CoreService
from app.core.models import Integration, IntegrationAction, ConfigurationButton
from app.core.display_service import DisplayService
from app.core.button_box_service import ButtonBoxService
from app.core.types import HttpStatusCode, NetworkResponse

class BaseIntegrationService:
    def __init__(self):
        # Core details
        self.id = None
        self.name = None
        self.description = None
        self.is_active = None
        self.configuration = None

        # Keeps these as None for any integrations that do not require a custom web panel for configuration
        self.url_prefix = None
        self.blueprint = None

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
                existing_integration.active = self.is_active # TODO in future, add an integration manager so we can delete this and just manage on a web page
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

    """
    This initialises anything specific to the service. Unlike the database initialise() method,
    this will be used by each individual service to initialise anything they need to do.
    
    Such as authenticating with an external API etc etc
    """

    def initialise_service(self):
        pass

    def get_actions(self):
        integration_actions = IntegrationAction.query.filter_by(integration_id=self.id).all()
        return integration_actions

    def add_action(self, name, description, configuration):
        try:
            action = IntegrationAction(name=name, description=description, configuration=configuration, integration_id=self.id)
            self.db.session.add(action)
            self.db.session.commit()
        except:
            return NetworkResponse().with_error("Failed to add action", HttpStatusCode.InternalServerError)

        return NetworkResponse()

    def edit_action(self, name, description, configuration):
        raise NotImplementedError()  # TODO IN HERE

    def remove_action(self, id):
        try:
            buttons = ConfigurationButton.query.filter_by(integration_action_id=id).all()
            for button in buttons:
                self.db.session.delete(button)

            action = IntegrationAction.query.filter_by(id=id).first()
            self.db.session.delete(action)
            self.db.session.commit()
        except:
            return NetworkResponse().with_error("Failed to remove action", HttpStatusCode.InternalServerError)

        return NetworkResponse()

    def handle_action(self, action: IntegrationAction, display: DisplayService, button_box: ButtonBoxService):
        pass
