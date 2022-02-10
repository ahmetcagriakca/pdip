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

    def get_iterator(self, integration: IntegrationBase, limit):
        source_context = self.provider.get_context_by_config(
            config=integration.SourceConnections.BigData.Connection)
        query = integration.SourceConnections.BigData.Query
        if integration.SourceConnections.BigData.Query is None or integration.SourceConnections.BigData.Query == '':
            schema = integration.SourceConnections.BigData.Schema
            table = integration.SourceConnections.BigData.ObjectName
            if schema is None or schema == '' or table is None or table == '':
                raise Exception(f"Source Schema and Table required. {schema}.{table}")
            source_columns = integration.SourceConnections.Columns
            if source_columns is not None and len(source_columns) > 0:
                source_column_rows = [column.Name for column in source_columns]
                columns_query = ",".join(source_column_rows)
                query = source_context.dialect.get_table_select_query(selected_rows=columns_query, schema=schema,
                                                                      table=table)
            else:
                query = source_context.dialect.get_table_select_query(selected_rows='*', schema=schema, table=table)
        iterator = source_context.get_iterator(query, limit)
        return iterator

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
