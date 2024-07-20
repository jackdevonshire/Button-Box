from abc import ABC, abstractmethod
from display_service import DisplayService

class DefaultButton(ABC):
    def __init__(self, event_configuration, display_service: DisplayService):
        self.event_configuration = event_configuration
        self.display_service = display_service

    @abstractmethod
    def handle(self):
        raise NotImplementedError()
