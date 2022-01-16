from unittest import TestCase

from pdip.integrator.connection.domain.enums import ConnectorTypes
from pdip.integrator.connection.types.sql.base import SqlProvider


class TestMssqlConnection(TestCase):
    def setUp(self):
        self.context = SqlProvider().get_context(
            connector_type=ConnectorTypes.MSSQL,
            host='localhost,1433', port=None,
            user='pdi', password='pdi!123456',
            database='test_pdi')

    def tearDown(self):
        return super().tearDown()

    def test_mssql_connection(self):
        try:
            self.context.connector.connect()
            self.context.connector.disconnect()
        except Exception as ex:
            print(ex)
            raise

    def test_create_and_drop_table(self):
        try:
            self.context.execute('''CREATE TABLE test_pdi.test_source (
	Id INT NULL,
	Name varchar(100) NULL
)''')
        except Exception as ex:
            print(ex)
            raise
        finally:

            self.context.execute('''DROP TABLE test_pdi.test_source''')

    def test_data(self):
        try:
            self.context.execute('''CREATE TABLE test_pdi.test_source (
    Id INT NULL,
    Name varchar(100) NULL
)''')
            self.context.execute('''insert into test_pdi.test_source(Id,Name) values(1,'test')''')
            data = self.context.fetch_query('''select * from test_pdi.test_source''')
            assert len(data) == 1
            assert data[0]["Id"] == 1
            assert data[0]["Name"] == 'test'

            self.context.execute('''update test_pdi.test_source set Name='Update' where Id=1''')
            data = self.context.fetch_query('''select * from test_pdi.test_source''')
            assert data[0]["Id"] == 1
            assert data[0]["Name"] == 'Update'
            self.context.execute('''delete from test_pdi.test_source where Id=1''')
            data = self.context.fetch_query('''select * from test_pdi.test_source''')
            assert len(data) == 0
        except Exception as ex:
            print(ex)
            raise
        finally:
            self.context.execute('''DROP TABLE test_pdi.test_source''')

    def test_check_schema_and_tables(self):
        try:
            schemas = self.context.dialect.get_schemas()
            for schema in schemas:
                print("schema: %s" % schema)
                for table_name in self.context.dialect.get_tables(schema=schema):
                    print("\tTable: %s" % table_name)
                    for column in self.context.dialect.get_columns(object_name=table_name, schema=schema):
                        print("\t\tColumn: %s" % column)
                for view_name in self.context.dialect.get_views(schema=schema):
                    print("\tView: %s" % view_name)
                    for column in self.context.dialect.get_columns(object_name=view_name, schema=schema):
                        print("\t\tColumn: %s" % column)
        except Exception as ex:
            print(ex)
            raise
