from flask_sqlalchemy import SQLAlchemy
from app.core.models import Integration, IntegrationAction, Configuration, ConfigurationButton, Setting

class KeyService:
    def __init__(self, db: SQLAlchemy):
        self.db = db