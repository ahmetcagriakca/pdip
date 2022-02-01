from typing import List

from injector import inject

from pdip.exceptions import NotSupportedFeatureException
from pdip.integrator.connection.base import ConnectionSourceAdapter
from pdip.integrator.connection.types.webservice.base import WebServiceProvider
from pdip.integrator.integration.domain.base import IntegrationBase


class WebServiceSourceAdapter(ConnectionSourceAdapter):
    @inject
    def __init__(self,
                 provider: WebServiceProvider,
                 ):
        self.provider = provider

    def get_source_data_count(self, integration: IntegrationBase) -> int:
        raise NotSupportedFeatureException(f"{self.__class__.__name__} get_source_data_count")

    def get_source_data(self, integration: IntegrationBase) -> List[any]:
        raise NotSupportedFeatureException(f"{self.__class__.__name__} get_source_data")

    def get_source_data_with_paging(self, integration: IntegrationBase, start, end) -> List[any]:
        raise NotSupportedFeatureException(f"{self.__class__.__name__} get_source_data_with_paging")
