from unittest import TestCase

from sqlalchemy import Column, Table, MetaData

from pdip.integrator.connection.domain.enums import ConnectorTypes
from pdip.integrator.connection.types.sql.base import SqlProvider
from pdip.logging.loggers.console import ConsoleLogger


class TestPostgresqlConnection(TestCase):
    def setUp(self):
        self.context = SqlProvider().get_context(
            connector_type=ConnectorTypes.POSTGRESQL,
            host='localhost', port='5434',
            user='pdi', password='pdi!123456',
            database='test_pdi'
        )

    def tearDown(self):
        return super().tearDown()

    def test_connection(self):
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
            assert data[0]["id"] == 1
            assert data[0]["name"] == 'test'

            self.context.execute('''update test_pdi.test_source set Name='Update' where Id=1''')
            data = self.context.fetch_query('''select * from test_pdi.test_source''')
            assert data[0]["id"] == 1
            assert data[0]["name"] == 'Update'
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

    def test_integration(self):
        try:
            engine = self.context.connector.get_engine()
            self.context.execute('''CREATE TABLE test_pdi.test_source (
                Id INT NULL,
                Name varchar(100) NULL
            )''')
            self.context.execute('''insert into test_pdi.test_source(Id,Name) values(1,'test')''')
            TABLE_SPEC = [
                ('id'),
                ('name')
            ]

            TABLE_NAME = 'test_source'
            TABLE_SCHEMA = 'test_pdi'
            columns = [Column(n) for n in TABLE_SPEC]
            table = Table(TABLE_NAME, MetaData(), schema=TABLE_SCHEMA, *columns)
            from sqlalchemy.orm import sessionmaker, Session
            _SessionFactory = sessionmaker(bind=engine)
            session = _SessionFactory()

            qu = table.select().limit(1).offset(0)
            res = session.execute(qu)
            result = list(res)
            session.commit()
            assert result[0][0] == 1
        except Exception as ex:
            ConsoleLogger().exception(ex)
            raise
        finally:
            self.context.execute('''DROP TABLE test_pdi.test_source''')
