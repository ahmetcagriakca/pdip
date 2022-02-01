from typing import List

from injector import inject

from pdip.integrator.connection.base import ConnectionSourceAdapter
from pdip.integrator.connection.types.bigdata.base import BigDataProvider
from pdip.integrator.integration.domain.base import IntegrationBase


class BigDataSourceAdapter(ConnectionSourceAdapter):
    @inject
    def __init__(self,
                 provider: BigDataProvider,
                 ):
        self.provider = provider

    def get_source_data_count(self, integration: IntegrationBase) -> int:
        source_context = self.provider.get_context_by_config(
            config=integration.SourceConnections.BigData.Connection)
        query = integration.SourceConnections.BigData.Query
        if integration.SourceConnections.BigData.Query is None or integration.SourceConnections.BigData.Query == '':
            schema = integration.SourceConnections.BigData.Schema
            table = integration.SourceConnections.BigData.ObjectName
            if schema is None or schema == '' or table is None or table == '':
                raise Exception(f"Source Schema and Table required. {schema}.{table}")
            query = source_context.dialect.get_table_select_query(selected_rows='*', schema=schema, table=table)
        data_count = source_context.get_table_count(query=query)
        return data_count

    def get_source_data(self, integration: IntegrationBase) -> List[any]:
        source_context = self.provider.get_context_by_config(
            config=integration.SourceConnections.BigData.Connection)
        query = integration.SourceConnections.BigData.Query
        if integration.SourceConnections.BigData.Query is None or integration.SourceConnections.BigData.Query == '':
            schema = integration.SourceConnections.BigData.Schema
            table = integration.SourceConnections.BigData.ObjectName
            if schema is None or schema == '' or table is None or table == '':
                raise Exception(f"Source Schema and Table required. {schema}.{table}")
            query = source_context.dialect.get_table_select_query(selected_rows='*', schema=schema, table=table)
        data = source_context.get_table_data(query=query)
        return data

    def get_source_data_with_paging(self, integration: IntegrationBase, start, end) -> List[any]:
        source_context = self.provider.get_context_by_config(
            config=integration.SourceConnections.BigData.Connection)
        query = integration.SourceConnections.BigData.Query
        if integration.SourceConnections.BigData.Query is None or integration.SourceConnections.BigData.Query == '':
            schema = integration.SourceConnections.BigData.Schema
            table = integration.SourceConnections.BigData.ObjectName
            if schema is None or schema == '' or table is None or table == '':
                raise Exception(f"Source Schema and Table required. {schema}.{table}")
            query = source_context.dialect.get_table_select_query(selected_rows='*', schema=schema, table=table)
        data = source_context.get_table_data_with_paging(
            query=query,
            start=start,
            end=end
        )
        return data
