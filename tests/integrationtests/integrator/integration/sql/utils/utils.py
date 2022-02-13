from random import randint

from pdip.integrator.connection.types.sql.base import SqlProvider


class TestSqlUtils:
    @classmethod
    def prepare_test_data(cls, connection, data_count):
        context = SqlProvider().get_context_by_config(connection)
        test_data = []
        for index, i in enumerate(range(data_count)):
            test_data.append([index, str(randint(0, 10))])
        context.execute('''CREATE TABLE test_pdi.test_source (
        Id INT NULL,
        Name varchar(100) NULL
        )''')

        indexer_array = []
        indexer = context.dialect.indexer()
        for index in range(2):
            column_indexer = indexer.format(index=index)
            indexer_array.append(column_indexer)
        values_query = ','.join(indexer_array)
        context.execute_many(f'''insert into  test_pdi.test_source values({values_query}) ''', test_data)

    @classmethod
    def prepare_test_data_with_info(cls, connection,schema,table,columns, data_count):
        context = SqlProvider().get_context_by_config(connection)
        test_data = []
        for index, i in enumerate(range(data_count)):
            test_data.append([index, str(randint(0, 10))])
        context.create_table(schema=schema, table=table, columns=columns)

        column_names = [c.Name for c in columns]

        target_query = context.get_target_query(
            query=None,
            target_columns=column_names,
            source_columns=column_names,
            schema=schema,
            table=table,
            source_column_count=len(column_names)
        )
        context.execute_many(target_query, test_data)