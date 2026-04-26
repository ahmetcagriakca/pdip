from random import randint

from pdip.integrator.connection.domain.types.bigdata.base import ConnectionBigDataBase
from pdip.integrator.connection.types.bigdata.base import BigDataProvider
from pdip.integrator.integration.domain.base import IntegrationBase, IntegrationConnectionBase
from pdip.integrator.operation.domain import OperationBase, OperationIntegrationBase


class TestBigDataUtils:
    """Helper for the bigdata integration suite — mirrors
    ``TestSqlUtils`` but routes through ``BigDataProvider`` /
    ``BigDataContext`` so the same end-to-end shape (prepare data
    → integrate → drop) works for the Impala adapter under
    ``tests/environments/bigdata/impala/``.
    """

    @classmethod
    def prepare_test_data_with_info(cls, connection, schema, table, columns, data_count):
        context = BigDataProvider().get_context_by_config(connection)
        test_data = []
        for index, _ in enumerate(range(data_count)):
            test_data.append([index, str(randint(0, 10))])
        context.create_table(schema=schema, table=table, columns=columns, if_exists='DoNothing')

        column_names = [c.Name for c in columns]
        target_query = context.get_target_query(
            query=None,
            target_columns=column_names,
            source_columns=column_names,
            schema=schema,
            table=table,
            source_column_count=len(column_names),
        )

        max_limit = 10000
        data_length = len(test_data)
        if data_length > max_limit:
            range_count = int(data_length / max_limit)
            for i in range(range_count):
                min_index = i * max_limit
                max_index = (i + 1) * max_limit
                temp = test_data[min_index:max_index]
                context.execute_many(target_query, temp)
        else:
            context.execute_many(target_query, test_data)

    @classmethod
    def get_operation(
            cls, connection, source_schema, source_table,
            target_schema, target_table, target_columns,
            limit, process_count,
    ) -> OperationBase:
        context = BigDataProvider().get_context_by_config(connection)
        create_query = context.dialect.get_create_table_query(
            schema=target_schema,
            table=target_table,
            columns=target_columns,
            if_exists='DoNothing',
        )
        drop_query = context.dialect.get_drop_table_query(
            schema=target_schema,
            table=target_table,
            if_not_exists='DoNothing',
        )

        operation = OperationBase(
            Name='TestBigDataOperation',
            Integrations=[
                OperationIntegrationBase(
                    Name='TestIntegrationCreateTable',
                    Order=1,
                    Limit=0,
                    ProcessCount=0,
                    Integration=IntegrationBase(
                        TargetConnections=IntegrationConnectionBase(
                            ConnectionName=connection.Name,
                            ConnectionType=connection.ConnectionType,
                            BigData=ConnectionBigDataBase(
                                Connection=connection,
                                Query=create_query,
                            ),
                        ),
                    ),
                ),
                OperationIntegrationBase(
                    Name='TestIntegrationLoadData',
                    Order=2,
                    Limit=limit,
                    ProcessCount=process_count,
                    Integration=IntegrationBase(
                        IsTargetTruncate=True,
                        SourceConnections=IntegrationConnectionBase(
                            ConnectionName=connection.Name,
                            ConnectionType=connection.ConnectionType,
                            BigData=ConnectionBigDataBase(
                                Connection=connection,
                                Schema=source_schema,
                                ObjectName=source_table,
                            ),
                        ),
                        TargetConnections=IntegrationConnectionBase(
                            ConnectionName=connection.Name,
                            ConnectionType=connection.ConnectionType,
                            BigData=ConnectionBigDataBase(
                                Connection=connection,
                                Schema=target_schema,
                                ObjectName=target_table,
                            ),
                        ),
                    ),
                ),
                OperationIntegrationBase(
                    Name='TestIntegrationDropTable',
                    Order=3,
                    Limit=0,
                    ProcessCount=0,
                    Integration=IntegrationBase(
                        TargetConnections=IntegrationConnectionBase(
                            ConnectionName=connection.Name,
                            ConnectionType=connection.ConnectionType,
                            BigData=ConnectionBigDataBase(
                                Connection=connection,
                                Query=drop_query,
                            ),
                        ),
                    ),
                ),
            ],
        )
        return operation
