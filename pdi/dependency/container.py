from .service_provider import ServiceProvider
# from ..api.flask_app_wrapper import FlaskAppWrapper


class DependencyContainer:
    Instance: ServiceProvider = None

    @classmethod
    def initialize_service(cls, root_directory):
        cls.Instance = ServiceProvider(root_directory)
        cls.Instance.import_controllers()
        return DependencyContainer
    #
    # @classmethod
    # def run_api(cls):
    #     DependencyContainer.Instance.injector.get(FlaskAppWrapper).run()
    #
    # @classmethod
    # def get_api_test_client(cls):
    #     DependencyContainer.Instance.injector.get(FlaskAppWrapper).test_client()