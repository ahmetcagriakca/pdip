from injector import inject

from pdip.integrator.operation.domain import OperationIntegrationBase
from ...base import Initializer
from ....dependency import IScoped
from ....dependency.container import DependencyContainer


class OperationIntegrationInitializer(Initializer):
    @inject
    def initialize(self, operation_integration: OperationIntegrationBase) -> int:
        pass


class OperationIntegrationInitializerFactory(IScoped):
    @inject
    def __init__(self
                 ):
        pass

    def get_initializer(self) -> OperationIntegrationInitializer:
        subclasses = OperationIntegrationInitializer.__subclasses__()
        if subclasses is not None and len(subclasses) > 0:
            initializer_class = subclasses[0]
            initializer = DependencyContainer.Instance.get(initializer_class)
            return initializer
