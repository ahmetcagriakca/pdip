from typing import List

from injector import inject
from pandas import DataFrame

from pdip.integrator.connection.base import ConnectionTargetAdapter
from pdip.integrator.connection.types.sql.base import SqlProvider
from pdip.integrator.integration.domain.base import IntegrationBase


class SqlTargetAdapter(ConnectionTargetAdapter):
    @inject
    def __init__(self,
                 provider: SqlProvider,
                 ):
        self.provider = provider

    def clear_data(self, integration: IntegrationBase) -> int:
        target_context = self.provider.get_context_by_config(
            config=integration.TargetConnections.Sql.Connection)
        truncate_affected_rowcount = target_context.truncate_table(schema=integration.TargetConnections.Sql.Schema,
                                                                   table=integration.TargetConnections.Sql.ObjectName)
        return truncate_affected_rowcount

    def prepare_data(self, target_context, integration: IntegrationBase, source_data: any) -> List[any]:
        columns = integration.SourceConnections.Columns
        if columns is not None:
            source_columns = [(column.Name) for column in columns]
        elif columns is None:
            source_columns = list(source_data[0].keys())
        if isinstance(source_data, DataFrame):
            data = source_data[source_columns]
            prepared_data = data.values.tolist()
        else:
            prepared_data = target_context.prepare_insert_row(
                data=source_data,
                columns=source_columns
            )
        return prepared_data

    def write_target_data(self, integration: IntegrationBase, source_data: List[any]) -> int:
        if source_data is not None and len(source_data) > 0:
            target_context = self.provider.get_context_by_config(
                config=integration.TargetConnections.Sql.Connection
            )
            prepared_data = self.prepare_data(
                target_context=target_context,
                integration=integration,
                source_data=source_data
            )
            prepared_target_query = target_context.get_target_query(
                query=integration.TargetConnections.Sql.Query,
                source_columns=[column.Name for column in integration.SourceConnections.Columns],
                target_columns=[column.Name for column in integration.TargetConnections.Columns],
                schema=integration.TargetConnections.Sql.Schema,
                table=integration.TargetConnections.Sql.ObjectName,
                source_column_count=len(prepared_data[0])
            )
            affected_row_count = target_context.execute_many(
                query=prepared_target_query,
                data=prepared_data
            )
            return affected_row_count
        else:
            return 0

    def do_target_operation(self, integration: IntegrationBase) -> int:
        target_context = self.provider.get_context_by_config(
            config=integration.TargetConnections.Sql.Connection)

        affected_rowcount = target_context.execute(query=integration.TargetConnections.Sql.Query)
        return affected_rowcount
