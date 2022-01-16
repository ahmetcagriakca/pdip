from injector import inject

from .in_memory_context import InMemoryContext
from .in_memory_policy import InMemoryPolicy
from ....domain.bigdata import BigDataConnectionConfiguration
from ....domain.enums import ConnectorTypes, ConnectionTypes
from ....domain.inmemory import InMemoryConnectionConfiguration
from ......dependency import IScoped


class InMemoryProvider(IScoped):
    @inject
    def __init__(self):
        pass

    def __initialize_context(self, config: BigDataConnectionConfiguration):
        policy = InMemoryPolicy(config=config)
        context = InMemoryContext(policy=policy)
        return context

    def get_context_by_config(self, config: BigDataConnectionConfiguration) -> InMemoryContext:
        return self.__initialize_context(config=config)

    def get_context(
            self,
            connector_type: ConnectorTypes,
            database: str) -> InMemoryContext:
        """
        Creating Context
        """
        if connector_type == connector_type.SqLite:
            config = InMemoryConnectionConfiguration(
                ConnectionType=ConnectionTypes.InMemory,
                ConnectorType=ConnectorTypes.SqLite,
                Database=database
            )
        else:
            raise Exception(f"{connector_type.name} connector type not supported")

        return self.__initialize_context(config=config)
