from unittest import TestCase

from pdip.integrator.connection.domain.enums import ConnectorTypes
from pdip.integrator.connection.types.sql.base import SqlProvider


class TestPostgresqlConnection(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        return super().tearDown()

    def test_connection(self):
        try:
            self.database_context = SqlProvider().get_context(
                connector_type=ConnectorTypes.POSTGRESQL,
                host='localhost', port='5434',
                user='pdi', password='pdi!123456',
                database='test_pdi')
            self.database_context.connector.connect()
        except Exception as ex:
            print(ex)
            raise

    def test_create_and_drop_table(self):
        try:
            self.database_context = SqlProvider().get_context(
                connector_type=ConnectorTypes.POSTGRESQL,
                host='localhost', port='5434',
                user='pdi', password='pdi!123456',
                database='test_pdi')
            self.database_context.execute('''CREATE TABLE test_pdi.test_source (
	Id INT NULL,
	Name varchar(100) NULL
)''')
        except Exception as ex:
            print(ex)
            raise
        finally:
            self.database_context.execute('''DROP TABLE test_pdi.test_source''')


    def test_data(self):
        try:
            self.database_context = SqlProvider().get_context(
                connector_type=ConnectorTypes.POSTGRESQL,
                host='localhost', port='5434',
                user='pdi', password='pdi!123456',
                database='test_pdi')
            self.database_context.execute('''CREATE TABLE test_pdi.test_source (
    Id INT NULL,
    Name varchar(100) NULL
)''')
            self.database_context.execute('''insert into test_pdi.test_source(Id,Name) values(1,'test')''')
            data = self.database_context.fetch('''select * from test_pdi.test_source''')
            assert len(data) == 1
            assert data[0]["id"] == 1
            assert data[0]["name"] == 'test'

            self.database_context.execute('''update test_pdi.test_source set Name='Update' where Id=1''')
            data = self.database_context.fetch('''select * from test_pdi.test_source''')
            assert data[0]["id"] == 1
            assert data[0]["name"] == 'Update'
            self.database_context.execute('''delete from test_pdi.test_source where Id=1''')
            data = self.database_context.fetch('''select * from test_pdi.test_source''')
            assert len(data) == 0
        except Exception as ex:
            print(ex)
            raise
        finally:
            self.database_context.execute('''DROP TABLE test_pdi.test_source''')
