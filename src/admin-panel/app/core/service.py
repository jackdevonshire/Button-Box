from flask_sqlalchemy import SQLAlchemy
from app.core.models import Integration, IntegrationAction, Configuration, ConfigurationButton

class CoreService:
    def __init__(self, db: SQLAlchemy): # Will also need to import the different integrations here, and an integration factory
        self.db = db

    def connect(self):
        