import importlib

from injector import inject

from .web_service_connector import WebServiceConnector
from ....domain.webservice.base import WebServiceConnectionConfiguration
from ....domain.enums import ConnectorTypes


class WebServicePolicy:
    @inject
    def __init__(self, config: WebServiceConnectionConfiguration):
        self.config = config
        self.connector: WebServiceConnector = None
        self.connector_name = None
        connector_base_module = "pdip.integrator.connection.types.webservice.connectors"
        if self.config.ConnectorType == ConnectorTypes.Impala:
            connector_namespace = "soap"
            connector_name = "SoapConnector"
        else:
            raise Exception("Connector type not found")
        module = importlib.import_module(".".join([connector_base_module, connector_namespace]))
        connector_class = getattr(module, connector_name)
        if connector_class is not None:
            self.connector: WebServiceConnector = connector_class(config)
