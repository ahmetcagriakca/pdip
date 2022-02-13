import importlib

from injector import inject

from .big_data_connector import BigDataConnector
from .big_data_dialect import BigDataDialect
from ....domain.enums import ConnectorTypes
from ....domain.types.bigdata.configuration.base import BigDataConnectionConfiguration


class BigDataPolicy:
    @inject
    def __init__(self, config: BigDataConnectionConfiguration):
        self.config = config
        self.connector: BigDataConnector = None
        self.connector_name = None
        connector_base_module = "pdip.integrator.connection.types.bigdata.connectors"
        dialect_base_module = "pdip.integrator.connection.types.bigdata.dialects"
        if self.config.ConnectorType == ConnectorTypes.Impala:
            namespace = "impala"
            connector_name = "ImpalaConnector"
            dialect_name = "ImpalaDialect"
        else:
            raise Exception("Connector type not found")
        module = importlib.import_module(".".join([connector_base_module, namespace]))
        connector_class = getattr(module, connector_name)
        if connector_class is not None:
            self.connector: BigDataConnector = connector_class(self.config)
        module = importlib.import_module(".".join([dialect_base_module, namespace]))
        dialect_class = getattr(module, dialect_name)
        if dialect_class is not None:
            self.dialect: BigDataDialect = dialect_class(self.connector)
