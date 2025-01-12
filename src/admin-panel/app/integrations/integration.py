from app import db, app
import json
from flask_sqlalchemy import SQLAlchemy
from app.core.models import Integration

class BaseIntegrationService:
    def __init__(self, db: SQLAlchemy):
        # Core details
        self.id = None
        self.name = None
        self.description = None
        self.is_active = None
        self.configuration = None
        self.blueprint = None

        # Other setup
        self.db = db

    def initialise(self):
        with app.app_context():
            existing_integration = Integration.query.filter_by(id=self.id).first()
            if not existing_integration:
                new_integration = Integration(
                    id=self.id,
                    name=self.name,
                    description=self.description,
                    is_active=self.is_active,
                    configuration=json.dumps(self.configuration)
                )

                db.session.add(new_integration)
                db.session.commit()
