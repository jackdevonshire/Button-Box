from abc import ABC, abstractmethod


class DefaultButton(ABC):
    def __init__(self, event_configuration):
        self.event_configuration = event_configuration

    @abstractmethod
    def handle(self):
        raise NotImplementedError()
