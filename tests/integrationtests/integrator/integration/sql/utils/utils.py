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
        indexer = context.connector.get_target_query_indexer()
        for index in range(2):
            column_indexer = indexer.format(index=index)
            indexer_array.append(column_indexer)
        values_query = ','.join(indexer_array)
        context.execute_many(f'''insert into  test_pdi.test_source values({values_query}) ''', test_data)
