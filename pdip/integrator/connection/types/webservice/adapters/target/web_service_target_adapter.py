import json
from datetime import datetime
from typing import List

from injector import inject

from pdip.exceptions import NotSupportedFeatureException
from pdip.integrator.connection.base import ConnectionTargetAdapter
from pdip.integrator.connection.types.webservice.base import WebServiceProvider
from pdip.integrator.integration.domain.base import IntegrationBase
from pdip.json import date_time_parser


class WebServiceTargetAdapter(ConnectionTargetAdapter):
    @inject
    def __init__(self,
                 provider: WebServiceProvider,
                 ):
        self.provider = provider

    def clear_data(self, integration: IntegrationBase) -> int:
        raise NotSupportedFeatureException(f"{self.__class__.__name__} clear_data")

    def prepare_insert_row(self, data, columns):
        insert_rows = []
        for extracted_data in data:
            row = []
            for column in columns:
                column_data = extracted_data[column]
                row.append(column_data)

            insert_rows.append(tuple(row))
        return insert_rows

    def prepare_data(self, integration: IntegrationBase, source_data: any) -> List[any]:
        # columns = integration.SourceConnections.Columns
        # if columns is not None:
        #     source_columns = [(column.Name) for column in columns]
        # elif columns is None:
        #     source_columns = source_data[0].keys()
        # if isinstance(source_data, DataFrame):
        #     data = source_data[source_columns]
        #     prepared_data = data.values.tolist()
        # else:
        #     prepared_data = self.prepare_insert_row(data=source_data, columns=source_columns)
        # data = source_data[source_column_rows]
        # prepared_data = data.values.tolist()
        return source_data

    def prepare_target_query(self, integration: IntegrationBase, source_column_count: int) -> str:
        raise NotSupportedFeatureException(f"{self.__class__.__name__} prepare_target_query")

    def write_target_data(self, integration: IntegrationBase, prepared_data: List[any]) -> int:
        if prepared_data is not None and len(prepared_data) > 0:
            target_context = self.provider.get_context_by_config(
                config=integration.TargetConnections.WebService.Connection)
            affected_row_count = 0
            for d in prepared_data:
                request_data = integration.TargetConnections.WebService.RequestBody
                for key in d.keys():
                    request_data = target_context.replace_regex(request_data, key, f'{d[key]}')

                request_data = target_context.replace_regex(request_data, 'CurrentDate', f'{datetime.now()}')
                json_data = json.loads(request_data, object_hook=date_time_parser)
                request = target_context.prepare_request_auth(request=json_data)
                result = target_context.call_service(method=integration.TargetConnections.WebService.Method,
                                                     request=request)
                affected_row_count += 1
            return affected_row_count
        else:
            return 0

    def do_target_operation(self, integration: IntegrationBase) -> int:
        raise NotSupportedFeatureException(f"{self.__class__.__name__} do_target_operation")
