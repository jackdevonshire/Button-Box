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
# Several threads write (requests, actions, the activity log) - wait for locks rather than failing straight away
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {"connect_args": {"timeout": 15}}

# Connect the database
db = SQLAlchemy(app)

# Start the event bus first so everything after this can log activity
from app.core.events import event_bus
event_bus.start(app, db)

# Configure core routes
from app.core.controllers import core, button_box_service, core_service, display_service, integration_factory
app.register_blueprint(core)

# Configure the JSON API used by the web UI
from app.api import api
app.register_blueprint(api)

# Serve the web UI
from app.web import web
app.register_blueprint(web)

all_integrations = integration_factory.get_all_integrations()

# Create the database and tables, then bring older databases up to date
from app.core.migrations import run_migrations
with app.app_context():
    db.create_all()
    run_migrations(db)

# Now create all integrations in database, if they don't already exist
for integration in all_integrations:
    integration.initialise_database(db, core_service)
    print(f"Integration ({integration.name}) successfully initialised")

# Initialise default settings
from app.core.models import Setting, Configuration
with app.app_context():
    if db.session.get(Setting, "ButtonBoxIP") is None:
        print("Populating default setting values")
        db.session.add(Setting(key="ButtonBoxIP", value="", visible=True))
        db.session.commit()

    # The button box always needs an active configuration, so create one on first run
    if Configuration.query.count() < 1:
        print("No configurations found. Creating default configuration")
        default_configuration = Configuration(name="Default", description="Default configuration")
        db.session.add(default_configuration)
        db.session.commit()

    # Bring any auto-generated integration actions in line with the current configurations
    core_service.sync_integration_actions()

# Initialise all integrations - allows them to auth with external API's etc
for integration in all_integrations:
    integration.initialise_service()
    print(f"Integration ({integration.name}) ready to handle events")

# Get default/first current configuration in the key service
button_box_service.initialise()
