from sqlalchemy import MetaData
from sqlalchemy.orm import declarative_base

from ..provider import ServiceProvider


class DependencyContainer:
    Instance: ServiceProvider = None
    Base = declarative_base(metadata=MetaData())

    @classmethod
    def initialize_service(cls, root_directory):
        cls.Instance = ServiceProvider(root_directory)
        if cls.Instance.is_flask_api():
            cls.initialize_api()
        else:
            cls.Instance.initialize_injection()
        return DependencyContainer

    @classmethod
    def initialize_api(cls):
        cls.Instance.initialize_flask()
        cls.Instance.import_controllers()
        cls.Instance.initialize_api_injection()

    @classmethod
    def cleanup(cls):
        del cls.Base
        cls.Base = declarative_base(metadata=MetaData())
        del cls.Instance
