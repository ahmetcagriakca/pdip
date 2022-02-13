from abc import ABC, abstractmethod


class Seed(ABC):
    @abstractmethod
    def seed(self):
        pass
