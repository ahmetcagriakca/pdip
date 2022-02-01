from injector import inject

from .default_operation_execution_initializer import DefaultOperationExecutionInitializer
from .operation_execution_initializer import OperationExecutionInitializer
from ....dependency import IScoped
from ....dependency.provider import ServiceProvider


class OperationExecutionInitializerFactory(IScoped):
    @inject
    def __init__(
            self,
            service_provider: ServiceProvider
    ):
        self.service_provider = service_provider

    def get(self) -> OperationExecutionInitializer:
        subclasses = OperationExecutionInitializer.__subclasses__()
        if subclasses is not None and len(subclasses) > 0:
            if len(subclasses) > 1:
                initializer_classes = [subclass for subclass in subclasses if
                                       not isinstance(subclass, DefaultOperationExecutionInitializer)]
                initializer_class = initializer_classes[0]
            else:
                initializer_class = subclasses[0]
            initializer = self.service_provider.get(initializer_class)
            return initializer
