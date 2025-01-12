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
from app.core.controllers import core, button_box_service, core_service, display_service, integration_factory
app.register_blueprint(core)

# Configure integration routes
all_integrations = integration_factory.get_all_integrations()
for integration in all_integrations:
    if integration.blueprint:
        app.register_blueprint(integration.blueprint)
        print(f"Blueprint for ({integration.name}) successfully loaded")

# Create the database and tables
with app.app_context():
    db.create_all()

# Now create all integrations in database, if they don't already exist
for integration in all_integrations:
    integration.initialise_database()
    print(f"Integration ({integration.name}) successfully initialised")

# Initialise default settings
from app.core.models import Setting, Configuration, ConfigurationButton, Integration, IntegrationAction
with app.app_context():
    settings = Setting.query.all()
    if len(settings) < 1:
        print("Invalid settings detected. Populating default setting values")
        ip_setting = Setting(key="ButtonBoxIP", value="", visible=True)
        db.session.add(ip_setting)
        db.session.commit()

        # Add some demo data
        ksp_config = Configuration(name="Demo KSP Config", description="Configuration for launching rockets in Kerbal Space Program")
        launch_rocket_action = IntegrationAction(integration_id=1, name="Launch Rocket", description="Launches a rocket in KSP", configuration={
            "Keys": ["space"],
            "Press": True,
            "PressDuration": 0.5,
            "Release": False
        })
        abort_rocket_action = IntegrationAction(integration_id=1, name="Abort Rocket", description="Abort the rocket launch in KSP", configuration={
            "Keys": ["shift", "x"],
            "Press": True,
            "PressDuration": 0.5,
            "Release": False
        })
        db.session.add(ksp_config)
        db.session.add(launch_rocket_action)
        db.session.add(abort_rocket_action)
        db.session.commit()

        ksp_launch_button = ConfigurationButton(configuration_id=ksp_config.id, name="Launch Rocket", physical_key=1, event_type=0, integration_action_id=launch_rocket_action.id)
        ksp_abort_button = ConfigurationButton(configuration_id=ksp_config.id, name= "Abort Mission", physical_key=2, event_type=1, integration_action_id=abort_rocket_action.id)
        db.session.add(ksp_launch_button)
        db.session.add(ksp_abort_button)
        db.session.commit()

# Initialise all integrations - allows them to auth with external API's etc
for integration in all_integrations:
    integration.initialise_service()
    print(f"Integration ({integration.name}) ready to handle events")

# Get default/first current configuration in the key service
button_box_service.initialise()