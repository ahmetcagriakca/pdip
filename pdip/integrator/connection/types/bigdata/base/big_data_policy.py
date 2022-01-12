import importlib

from injector import inject

from .big_data_connector import BigDataConnector
from ....domain.bigdata import BigDataConnectionConfiguration
from ....domain.enums import ConnectorTypes


class BigDataPolicy:
    @inject
    def __init__(self, config: BigDataConnectionConfiguration):
        self.config = config
        self.connector: BigDataConnector = None
        self.connector_name = None
        connector_base_module = "pdip.integrator.connection.types.bigdata.connectors"
        if self.config.ConnectorType == ConnectorTypes.Impala:
            connector_namespace = "impala"
            connector_name = "ImpalaConnector"
        else:
            raise Exception("Connector type not found")
        module = importlib.import_module(".".join([connector_base_module, connector_namespace]))
        connector_class = getattr(module, connector_name)
        if connector_class is not None:
            self.connector: BigDataConnector = connector_class(config)
