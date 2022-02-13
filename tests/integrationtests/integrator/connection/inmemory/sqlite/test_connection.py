from unittest import TestCase

from pdip.integrator.connection.domain.enums import ConnectorTypes
from pdip.integrator.connection.types.inmemory.base import InMemoryProvider


class TestMssqlConnection(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        return super().tearDown()

    def test_mssql_connection(self):
        try:
            self.database_context = InMemoryProvider().get_context(
                connector_type=ConnectorTypes.SqLite,
                database='test_pdi.db'
            )
            self.database_context.connector.connect()
        except Exception as ex:
            print(ex)
            raise

    def test_create_and_drop_table(self):
        try:
            self.database_context = InMemoryProvider().get_context(
                connector_type=ConnectorTypes.SqLite,
                database='test_pdi'
            )
            self.database_context.execute('''CREATE TABLE main.test_source (
	Id INT NULL,
	Name varchar(100) NULL
)''')
        except Exception as ex:
            print(ex)
            raise
        finally:

            self.database_context.execute('''DROP TABLE main.test_source''')

    def test_data(self):
        try:
            self.database_context = InMemoryProvider().get_context(
                connector_type=ConnectorTypes.SqLite,
                database='test_pdi'
            )
            self.database_context.execute('''CREATE TABLE main.test_source (
    Id INT NULL,
    Name varchar(100) NULL
)''')
            self.database_context.execute('''insert into main.test_source(Id,Name) values(1,'test')''')
            data = self.database_context.fetch_query('''select * from main.test_source''')
            assert len(data) == 1
            assert data[0]["Id"] == 1
            assert data[0]["Name"] == 'test'

            self.database_context.execute('''update main.test_source set Name='Update' where Id=1''')
            data = self.database_context.fetch_query('''select * from main.test_source''')
            assert data[0]["Id"] == 1
            assert data[0]["Name"] == 'Update'
            self.database_context.execute('''delete from main.test_source where Id=1''')
            data = self.database_context.fetch_query('''select * from main.test_source''')
            assert len(data) == 0
        except Exception as ex:
            print(ex)
            raise
        finally:
            self.database_context.execute('''DROP TABLE main.test_source''')
