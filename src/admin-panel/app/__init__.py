# Core Imports
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

# Create the main flask app
app = Flask(__name__)

# Setup database path
base_dir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(base_dir, 'panel.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Connect the database
db = SQLAlchemy(app)

# Configure core routes
from app.core.controllers import core as core
app.register_blueprint(core)

# Configure integration routes
from app.integrations.integration_factory import IntegrationFactory
integration_factory = IntegrationFactory()

all_integrations = integration_factory.get_all_integrations()
for integration in all_integrations:
    app.register_blueprint(integration.blueprint)
    print(f"Blueprint for ({integration.name}) successfully loaded")

# Create the database and tables
with app.app_context():
    db.create_all()

# Now create all integrations in database, if they don't already exist
for integration in all_integrations:
    integration.initialise()
    print(f"Integration ({integration.name}) successfully initialised")

# Initialise default settings
from app.core.models import Setting
with app.app_context():
    settings = Setting.query.all()
    if len(settings) < 3:
        print("Invalid settings detected. Populating default setting values")

        ip_setting = Setting(key="ButtonBoxIP", value="", visible=True)
        default_configuration = Setting(key="DefaultConfigurationId", value="", visible=False)
        current_configuration = Setting(key="CurrentConfigurationId", value="", visible=False)

        db.session.add(ip_setting)
        db.session.add(default_configuration)
        db.session.add(current_configuration)
        db.session.commit()