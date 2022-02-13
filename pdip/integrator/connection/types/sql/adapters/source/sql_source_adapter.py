from typing import List

from injector import inject

from pdip.integrator.connection.base import ConnectionSourceAdapter
from pdip.integrator.connection.types.sql.base import SqlProvider
from pdip.integrator.integration.domain.base import IntegrationBase


class SqlSourceAdapter(ConnectionSourceAdapter):
    @inject
    def __init__(self,
                 provider: SqlProvider,
                 ):
        self.provider = provider

    def get_source_data_count(self, integration: IntegrationBase) -> int:
        source_context = self.provider.get_context_by_config(
            config=integration.SourceConnections.Sql.Connection)
        if integration.SourceConnections.Sql.Query is None or integration.SourceConnections.Sql.Query == '':
            schema = integration.SourceConnections.Sql.Schema
            table = integration.SourceConnections.Sql.ObjectName
            source_columns = integration.SourceConnections.Columns
            query = source_context.dialect.prepare_select_query(schema=schema, table=table, columns=source_columns)
            data_count = source_context.get_count_for_query(query=query)
        else:
            data_count = source_context.get_table_count(
                schema=integration.SourceConnections.Sql.Schema,
                table=integration.SourceConnections.Sql.ObjectName
            )
        return data_count

    def get_source_data(self, integration: IntegrationBase) -> List[any]:
        source_context = self.provider.get_context_by_config(
            config=integration.SourceConnections.Sql.Connection)
        query = integration.SourceConnections.Sql.Query
        if integration.SourceConnections.Sql.Query is None or integration.SourceConnections.Sql.Query == '':
            schema = integration.SourceConnections.Sql.Schema
            table = integration.SourceConnections.Sql.ObjectName
            source_columns = integration.SourceConnections.Columns
            query = source_context.dialect.prepare_select_query(schema=schema, table=table, columns=source_columns)
        data = source_context.get_data_for_query(query=query)
        return data

    def get_iterator(self, integration: IntegrationBase, limit):
        source_context = self.provider.get_context_by_config(
            config=integration.SourceConnections.Sql.Connection)
        query = integration.SourceConnections.Sql.Query
        if integration.SourceConnections.Sql.Query is None or integration.SourceConnections.Sql.Query == '':
            schema = integration.SourceConnections.Sql.Schema
            table = integration.SourceConnections.Sql.ObjectName
            source_columns = integration.SourceConnections.Columns
            query = source_context.dialect.prepare_select_query(schema=schema, table=table, columns=source_columns)
        iterator = source_context.get_iterator_for_query(query, limit)
        return iterator

    def get_source_data_with_paging(self, integration: IntegrationBase, start, end) -> List[any]:
        source_context = self.provider.get_context_by_config(
            config=integration.SourceConnections.Sql.Connection)
        query = integration.SourceConnections.Sql.Query
        if integration.SourceConnections.Sql.Query is None or integration.SourceConnections.Sql.Query == '':
            schema = integration.SourceConnections.Sql.Schema
            table = integration.SourceConnections.Sql.ObjectName
            source_columns = integration.SourceConnections.Columns
            query = source_context.dialect.prepare_select_query(schema=schema, table=table, columns=source_columns)

        data = source_context.get_data_with_paging(
            query=query,
            start=start,
            end=end
        )
        return data
