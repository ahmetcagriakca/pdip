from injector import inject

from .operation_initializer import OperationInitializer
from ....dependency import IScoped
from ....dependency.provider import ServiceProvider


class OperationInitializerFactory(IScoped):
    @inject
    def __init__(
            self,
            service_provider: ServiceProvider
    ):
        self.service_provider = service_provider

    def get_initializer(self) -> OperationInitializer:
        subclasses = OperationInitializer.__subclasses__()
        if subclasses is not None and len(subclasses) > 0:
            initializer_class = subclasses[0]
            initializer = self.service_provider.get(initializer_class)
            return initializer
