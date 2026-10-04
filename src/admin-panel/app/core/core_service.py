from flask_sqlalchemy import SQLAlchemy


class CoreService:
    def __init__(self, db: SQLAlchemy, button_box_service, integration_factory):
        self.db = db
        self.button_box_service = button_box_service
        self.integration_factory = integration_factory

    def get_nav_links(self):
        nav_links = {}
        for integration in self.integration_factory.get_all_integrations():
            if integration.is_active and integration.blueprint is not None and integration.url_prefix is not None:
                nav_links[integration.name] = {
                    "url": integration.url_prefix,
                    "description": integration.description,
                    "icon": integration.icon,
                }
        return nav_links

    def sync_integration_actions(self):
        for integration in self.integration_factory.get_all_integrations():
            integration.sync_actions()
