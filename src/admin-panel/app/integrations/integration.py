from app import db, app
import json
from flask_sqlalchemy import SQLAlchemy
from app.core.models import Integration, IntegrationAction
from app.core.display_service import DisplayService
from app.core.button_box_service import ButtonBoxService

class BaseIntegrationService:
    def __init__(self, db: SQLAlchemy):
        # Core details
        self.id = None
        self.name = None
        self.description = None
        self.is_active = None
        self.configuration = None

        # Keeps these as None for any integrations that do not require a custom web panel for configuration
        self.blueprint = None
        self.url_prefix = None

        # Other setup
        self.db = db

    """
    This initialises the configuration in the database, so that it is available to be seen in the UI if it is active
    """

    def initialise_database(self):
        with app.app_context():
            existing_integration = Integration.query.filter_by(id=self.id).first()
            if existing_integration:
                existing_integration.active = self.is_active
            else:
                new_integration = Integration(
                    id=self.id,
                    name=self.name,
                    description=self.description,
                    is_active=self.is_active,
                    configuration=json.dumps(self.configuration)
                )

                db.session.add(new_integration)
            db.session.commit()

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
        raise NotImplementedError()  # TODO IN HERE

    def edit_action(self, name, description, configuration):
        raise NotImplementedError()  # TODO IN HERE

    def remove_action(self, id):
        raise NotImplementedError()  # TODO IN HERE

    def handle_action(self, action: IntegrationAction, display: DisplayService, button_box: ButtonBoxService):
        pass
