from injector import inject

from .default_integrator_initializer import DefaultIntegratorInitializer
from .integrator_initializer import IntegratorInitializer
from ....dependency import IScoped
from ....dependency.provider import ServiceProvider


class IntegratorInitializerFactory(IScoped):
    @inject
    def __init__(
            self,
            service_provider: ServiceProvider
    ):
        self.service_provider = service_provider

    def get(self) -> IntegratorInitializer:
        subclasses = IntegratorInitializer.__subclasses__()
        if subclasses is not None and len(subclasses) > 0:
            if len(subclasses) > 1:
                initializer_classes = [subclass for subclass in subclasses if subclass != DefaultIntegratorInitializer]
                initializer_class = initializer_classes[0]
            else:
                initializer_class = subclasses[0]
            initializer = self.service_provider.get(initializer_class)
            return initializer
