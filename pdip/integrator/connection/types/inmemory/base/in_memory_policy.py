import importlib

from injector import inject

from .in_memory_connector import InMemoryConnector
from ....domain.enums import ConnectorTypes
from ....domain.inmemory import InMemoryConnectionConfiguration


class InMemoryPolicy:
    @inject
    def __init__(self, config: InMemoryConnectionConfiguration):
        self.config = config
        self.connector: InMemoryConnector = None
        self.connector_name = None
        connector_base_module = "pdip.integrator.connection.types.inmemory.connectors"
        if self.config.ConnectorType == ConnectorTypes.SqLite:
            connector_namespace = "sqlite"
            connector_name = "SqLiteConnector"
        else:
            raise Exception("Connector type not found")
        module = importlib.import_module(".".join([connector_base_module, connector_namespace]))
        connector_class = getattr(module, connector_name)
        if connector_class is not None:
            self.connector: InMemoryConnector = connector_class(self.config)
