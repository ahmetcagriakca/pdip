from injector import inject

from .default_integrator_event_manager import DefaultIntegratorEventManager
from .integrator_event_manager import IntegratorEventManager
from ....dependency import IScoped
from ....dependency.provider import ServiceProvider


class IntegratorEventManagerFactory(IScoped):
    @inject
    def __init__(
            self,
            service_provider: ServiceProvider
    ):
        self.service_provider = service_provider

    def get(self) -> IntegratorEventManager:
        subclasses = IntegratorEventManager.__subclasses__()
        if subclasses is not None and len(subclasses) > 0:
            if len(subclasses) > 1:
                initializer_classes = [subclass for subclass in subclasses if
                                       not isinstance(subclass, DefaultIntegratorEventManager)]
                initializer_class = initializer_classes[0]
            else:
                initializer_class = subclasses[0]
            initializer = self.service_provider.get(initializer_class)
            return initializer
