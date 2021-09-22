import os

from .service_provider import ServiceProvider
from ..api.app import FlaskAppWrapper


class DependencyContainer:
    Instance: ServiceProvider = None

    @classmethod
    def initialize_service(cls, root_directory):
        if root_directory is None:
            root_directory = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__))))
        cls.Instance = ServiceProvider(root_directory)

        cls.Instance.initialize_injection()
        cls.Instance.import_controllers()
        cls.Instance.configure_controller()

        return DependencyContainer
