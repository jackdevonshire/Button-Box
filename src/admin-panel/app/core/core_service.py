from flask_sqlalchemy import SQLAlchemy
from app.core.models import Integration, IntegrationAction, Configuration, ConfigurationButton, Setting
from app import app


class CoreService:
    def __init__(self, db: SQLAlchemy):
        self.db = db
        self.initalise()

    def initalise(self):
        with app.app_context():
            settings = Setting.query.all()
            if len(settings) < 3:
                print("No settings detected. Populating default setting values")

                ip_setting = Setting(key="ButtonBoxIP", value="", visible=True)
                default_configuration = Setting(key="DefaultConfigurationId", value="", visible=False)
                current_configuration = Setting(key="CurrentConfigurationId", value="", visible=False)

                self.db.session.add(ip_setting)
                self.db.session.add(default_configuration)
                self.db.session.add(current_configuration)
                self.db.session.commit()
