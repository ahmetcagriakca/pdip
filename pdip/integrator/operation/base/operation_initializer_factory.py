from injector import inject

from pdip.integrator.operation.domain import OperationBase
from ...base import Initializer
from ....dependency import IScoped
from ....dependency.container import DependencyContainer


class OperationInitializer(Initializer):
    @inject
    def initialize(self, operation: OperationBase) -> int:
        pass


class OperationInitializerFactory(IScoped):
    @inject
    def __init__(self
                 ):
        pass

    def get_initializer(self) -> OperationInitializer:
        subclasses = OperationInitializer.__subclasses__()
        if subclasses is not None and len(subclasses) > 0:
            initializer_class = subclasses[0]
            initializer = DependencyContainer.Instance.get(initializer_class)
            return initializer
