import os

from sqlalchemy import MetaData
from sqlalchemy.orm import declarative_base

from .service_provider import ServiceProvider


class DependencyContainer:
    Instance: ServiceProvider = None
    Base = declarative_base(metadata=MetaData())

    @classmethod
    def initialize_service(cls, root_directory):
        if root_directory is None:
            root_directory = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__))))
        cls.Instance = ServiceProvider(root_directory)

        cls.Instance.import_controllers()
        cls.Instance.initialize_injection()

        return DependencyContainer
