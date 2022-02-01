from typing import List

from injector import inject
from pandas import DataFrame

from pdip.integrator.connection.base import ConnectionTargetAdapter
from pdip.integrator.connection.types.bigdata.base import BigDataProvider
from pdip.integrator.integration.domain.base import IntegrationBase


class BigDataTargetAdapter(ConnectionTargetAdapter):
    @inject
    def __init__(self,
                 provider: BigDataProvider,
                 ):
        self.provider = provider

    def clear_data(self, integration: IntegrationBase) -> int:
        target_context = self.provider.get_context_by_config(
            config=integration.TargetConnections.BigData.Connection)
        truncate_affected_rowcount = target_context.truncate_table(schema=integration.TargetConnections.BigData.Schema,
                                                                   table=integration.TargetConnections.BigData.ObjectName)
        return truncate_affected_rowcount

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
        target_context = self.provider.get_context_by_config(
            config=integration.TargetConnections.BigData.Connection)

        columns = integration.SourceConnections.Columns
        if columns is not None and len(columns) > 0:
            source_columns = [(column.Name, column.Type) for column in
                              columns]
            prepared_target_query = target_context.prepare_target_query(
                column_rows=source_columns,
                query=integration.TargetConnections.BigData.Query
            )
        else:
            schema = integration.TargetConnections.BigData.Schema
            table = integration.TargetConnections.BigData.ObjectName
            if schema is None or schema == '' or table is None or table == '':
                raise Exception(f"Schema and table required. {schema}.{table}")
            indexer_array = []
            indexer = target_context.dialect.get_query_indexer()
            for index in range(source_column_count):
                column_indexer = indexer.format(index=index)
                indexer_array.append(column_indexer)
            values_query = ','.join(indexer_array)
            prepared_target_query = target_context.dialect.get_insert_query(values_query=values_query,
                                                                            schema=schema,
                                                                            table=table)
        return prepared_target_query

    def write_target_data(self, integration: IntegrationBase, prepared_data: List[any]) -> int:
        if prepared_data is not None and len(prepared_data) > 0:
            target_context = self.provider.get_context_by_config(
                config=integration.TargetConnections.BigData.Connection)

            prepared_target_query = self.prepare_target_query(integration=integration,
                                                              source_column_count=len(prepared_data[0]))
            affected_row_count = target_context.execute_many(query=prepared_target_query, data=prepared_data)
            return affected_row_count
        else:
            return 0

    def do_target_operation(self, integration: IntegrationBase) -> int:
        target_context = self.provider.get_context_by_config(
            config=integration.TargetConnections.BigData.Connection)

        affected_rowcount = target_context.execute(query=integration.TargetConnections.BigData.Query)
        return affected_rowcount
