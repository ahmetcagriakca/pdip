from injector import inject

from .integration_initializer import OperationIntegrationInitializer
from ....dependency import IScoped
from ....dependency.container import DependencyContainer


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
