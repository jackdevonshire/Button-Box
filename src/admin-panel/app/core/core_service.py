from flask_sqlalchemy import SQLAlchemy


class CoreService:
    def __init__(self, db: SQLAlchemy, button_box_service, integration_factory):
        self.db = db
        self.button_box_service = button_box_service
        self.integration_factory = integration_factory

    def sync_integration_actions(self):
        for integration in self.integration_factory.get_all_integrations():
            integration.sync_actions()
