from abc import ABCMeta, ABC, abstractmethod


class BaseConfig(ABC):
    __metaclass__ = ABCMeta

    @abstractmethod
    def is_valid(self):
        pass
