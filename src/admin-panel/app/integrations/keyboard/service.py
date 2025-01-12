from app.integrations.keyboard.controllers import bp_keyboard as bp_keyboard
from flask_sqlalchemy import SQLAlchemy
from app.core.models import Integration
import json
from app import db, app

class KeyboardService:
    def __init__(self, db: SQLAlchemy):
        # Core details
        self.id = 1
        self.name = "Keyboard"
        self.description = "An integration to simulate keyboard interactions on the server hosts machine"
        self.is_active = True
        self.configuration = {}

        # Other setup
        self.db = db

    def initalise(self):
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

    def get_blueprint(self):
        return bp_keyboard