from asyncio import Queue
from typing import List

from injector import inject
from pandas import DataFrame

from ..base import ConnectionAdapter
from ..types.sql.base import SqlProvider
from ...integration.domain.base import IntegrationBase


class SqlAdapter(ConnectionAdapter):
    @inject
    def __init__(self,
                 sql_provider: SqlProvider,
                 ):
        self.sql_provider = sql_provider

    def clear_data(self, integration: IntegrationBase) -> int:
        target_context = self.sql_provider.get_context_by_config(
            config=integration.TargetConnections.Sql.Connection)
        truncate_affected_rowcount = target_context.truncate_table(schema=integration.TargetConnections.Sql.Schema,
                                                                   table=integration.TargetConnections.Sql.ObjectName)
        return truncate_affected_rowcount

    def get_source_data_count(self, integration: IntegrationBase) -> int:

        source_context = self.sql_provider.get_context_by_config(
            config=integration.SourceConnections.Sql.Connection)
        query = integration.SourceConnections.Sql.Query
        if integration.SourceConnections.Sql.Query is None or integration.SourceConnections.Sql.Query == '':
            schema = integration.SourceConnections.Sql.Schema
            table = integration.SourceConnections.Sql.ObjectName
            if schema is None or schema == '' or table is None or table == '':
                raise Exception(f"Source Schema and Table required. {schema}.{table}")
            query = f'select * from {schema}.{table}'
        data_count = source_context.get_table_count(query=query)
        return data_count

    def get_source_data(self, integration: IntegrationBase) -> List[any]:
        source_context = self.sql_provider.get_context_by_config(
            config=integration.SourceConnections.Sql.Connection)
        query = integration.SourceConnections.Sql.Query
        if integration.SourceConnections.Sql.Query is None or integration.SourceConnections.Sql.Query == '':
            schema = integration.SourceConnections.Sql.Schema
            table = integration.SourceConnections.Sql.ObjectName
            if schema is None or schema == '' or table is None or table == '':
                raise Exception(f"Source Schema and Table required. {schema}.{table}")
            query = f'select * from {schema}.{table}'
        data = source_context.get_table_data(query=query)
        return data

    def get_source_data_with_paging(self, integration: IntegrationBase, start, end) -> List[any]:
        source_context = self.sql_provider.get_context_by_config(
            config=integration.SourceConnections.Sql.Connection)
        query = integration.SourceConnections.Sql.Query
        if integration.SourceConnections.Sql.Query is None or integration.SourceConnections.Sql.Query == '':
            schema = integration.SourceConnections.Sql.Schema
            table = integration.SourceConnections.Sql.ObjectName
            if schema is None or schema == '' or table is None or table == '':
                raise Exception(f"Source Schema and Table required. {schema}.{table}")
            query = f'select * from {schema}.{table}'
        data = source_context.get_table_data_with_paging(
            query=query,
            start=start,
            end=end
        )
        return data

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
        columns = integration.SourceConnections.Columns
        if columns is not None:
            source_columns = [(column.Name) for column in columns]
        elif columns is None:
            source_columns = source_data[0].keys()
        if isinstance(source_data, DataFrame):
            data = source_data[source_columns]
            prepared_data = data.values.tolist()
        else:
            prepared_data = self.prepare_insert_row(data=source_data, columns=source_columns)
        return prepared_data

    def prepare_target_query(self, integration: IntegrationBase, source_column_count: int) -> str:
        target_context = self.sql_provider.get_context_by_config(
            config=integration.TargetConnections.Sql.Connection)

        columns = integration.TargetConnections.Columns
        if columns is not None:
            target_columns = [(column.Name, column.Type) for column in
                              columns]
            prepared_target_query = target_context.prepare_target_query(
                column_rows=target_columns,
                query=integration.TargetConnections.Sql.Query)
        else:
            schema = integration.TargetConnections.Sql.Schema
            table = integration.TargetConnections.Sql.ObjectName
            if schema is None or schema == '' or table is None or table == '':
                raise Exception(f"Schema and table required. {schema}.{table}")
            indexer_array = []
            indexer = target_context.connector.get_target_query_indexer()
            for index in range(source_column_count):
                column_indexer = indexer.format(index=index)
                indexer_array.append(column_indexer)
            values_query = ','.join(indexer_array)
            prepared_target_query = f'insert into {schema}.{table} values({values_query})'
        return prepared_target_query

    def write_target_data(self, integration: IntegrationBase, prepared_data: List[any]) -> int:
        if prepared_data is not None and len(prepared_data) > 0:
            target_context = self.sql_provider.get_context_by_config(
                config=integration.TargetConnections.Sql.Connection)

            prepared_target_query = self.prepare_target_query(integration=integration,
                                                              source_column_count=len(prepared_data[0]))
            affected_row_count = target_context.execute_many(query=prepared_target_query, data=prepared_data)
            return affected_row_count
        else:
            return 0

    def do_target_operation(self, integration: IntegrationBase) -> int:
        target_context = self.sql_provider.get_context_by_config(
            config=integration.TargetConnections.Sql.Connection)

        affected_rowcount = target_context.execute(query=integration.TargetConnections.Sql.Query)
        return affected_rowcount
