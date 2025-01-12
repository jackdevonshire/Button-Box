from flask_sqlalchemy import SQLAlchemy
from app.core.models import Integration, IntegrationAction, Configuration, ConfigurationButton, Setting
from app import app


class CoreService:
    def __init__(self, db: SQLAlchemy):
        self.db = db