from sqlalchemy import MetaData
from sqlalchemy.orm import declarative_base

from ..provider import ServiceProvider


class DependencyContainer:
    Instance: ServiceProvider = None
    Base = declarative_base(metadata=MetaData())

    @classmethod
    def initialize_service(cls,
                           root_directory=None,
                           configurations: [] = None,
                           excluded_modules: [] = None,
                           initialize_flask: bool = True):
        try:
            cls.Instance = ServiceProvider(root_directory=root_directory,
                                           configurations=configurations,
                                           excluded_modules=excluded_modules)
            cls.Instance.initialize_injection(initialize_flask=initialize_flask)
        except:
            cls.cleanup()
            raise

    @classmethod
    def cleanup(cls):

        if cls.Base is not None:
            del cls.Base
            cls.Base = declarative_base(metadata=MetaData())
        if hasattr(cls, 'Instance') and cls.Instance is not None:
            del cls.Instance
