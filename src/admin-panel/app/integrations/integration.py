from app import db, app
import json
from flask_sqlalchemy import SQLAlchemy
from app.core.models import Integration, IntegrationAction


class BaseIntegrationService:
    def __init__(self, db: SQLAlchemy):
        # Core details
        self.id = None
        self.name = None
        self.description = None
        self.is_active = None
        self.configuration = None
        self.blueprint = None
        self.url_prefix = None

        # Other setup
        self.db = db

    def initialise(self):
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


    def get_actions(self):
        integration_actions = IntegrationAction.query.filter_by(integration_id=self.id).all()
        return integration_actions

    def add_action(self, name, description, configuration):
        raise NotImplementedError() # TODO IN HERE

    def edit_action(self, name, description, configuration):
        raise NotImplementedError() # TODO IN HERE

    def remove_action(self, id):
        raise NotImplementedError() # TODO IN HERE

    def handle_action(self, action:IntegrationAction):
        pass