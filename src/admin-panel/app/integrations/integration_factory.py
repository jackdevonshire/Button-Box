from app import db

# Import integration services
from app.integrations.keyboard.service import KeyboardService

# List all integrations here
ALL_INTEGRATIONS = [
    KeyboardService(db)
]


class IntegrationFactory:
    def get_all_integrations(self):
        return ALL_INTEGRATIONS