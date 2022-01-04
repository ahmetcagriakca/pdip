from abc import ABC, abstractmethod


class Initializer(ABC):
    @abstractmethod
    def initialize(self):
        pass
