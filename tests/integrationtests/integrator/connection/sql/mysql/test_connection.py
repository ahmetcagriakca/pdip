from unittest import TestCase

from sqlalchemy import Column, Table, MetaData

from pdip.integrator.connection.domain.authentication.basic import ConnectionBasicAuthentication
from pdip.integrator.connection.domain.base import ConnectionColumnBase
from pdip.integrator.connection.domain.enums import ConnectorTypes, ConnectionTypes
from pdip.integrator.connection.domain.server.base import ConnectionServer
from pdip.integrator.connection.domain.types.sql.configuration.base import SqlConnectionConfiguration
from pdip.integrator.connection.types.sql.base import SqlProvider
from pdip.logging.loggers.console import ConsoleLogger
from tests.integrationtests.integrator.integration.sql.utils import TestSqlUtils


class TestMysqlConnection(TestCase):
    def setUp(self):
        self.connection = SqlConnectionConfiguration(
            Name='TestConnection',
            ConnectionType=ConnectionTypes.Sql,
            ConnectorType=ConnectorTypes.MYSQL,
            Server=ConnectionServer(
                Host='localhost',
                Port='3306'
            ),
            Database='test_pdi',
            BasicAuthentication=ConnectionBasicAuthentication(
                User='pdi',
                Password='pdi!123456'
            )
        )
        self.context = SqlProvider().get_context_by_config(self.connection)
        self.source_schema = 'test_pdi'
        self.source_table = 'TEST_SOURCE'
        self.source_columns = [
            ConnectionColumnBase(Name='ID', Type='INT'),
            ConnectionColumnBase(Name='NAME', Type='varchar(100)'),
        ]
        self.target_schema = 'test_pdi'
        self.target_table = 'TEST_TARGET'
        self.target_columns = [
            ConnectionColumnBase(Name='ID', Type='INT'),
            ConnectionColumnBase(Name='NAME', Type='varchar(100)'),
        ]

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
            self.context.create_table(schema=self.source_schema, table=self.source_table, columns=self.source_columns)
        except Exception as ex:
            print(ex)
            raise
        finally:
            self.context.drop_table(
                schema=self.source_schema,
                table=self.source_table,
            )

    def test_data(self):
        try:
            self.context.create_table(schema=self.source_schema, table=self.source_table, columns=self.source_columns)
            self.context.execute(
                f'''insert into  {self.context.dialect.mark_to_object(self.source_schema)}.{self.context.dialect.mark_to_object(self.source_table)} values(1,'test')''')
            data = self.context.get_table_data(schema=self.source_schema, table=self.source_table)
            assert len(data) == 1
            assert data[0]["ID"] == 1
            assert data[0]["NAME"] == 'test'

            self.context.execute(
                f'''update  {self.context.dialect.mark_to_object(self.source_schema)}.{self.context.dialect.mark_to_object(self.source_table)} set {self.context.dialect.mark_to_object("NAME")}='Update' where {self.context.dialect.mark_to_object("ID")}=1''')
            data = self.context.get_table_data(schema=self.source_schema, table=self.source_table)
            assert data[0]["ID"] == 1
            assert data[0]["NAME"] == 'Update'
            self.context.execute(
                f'''delete from  {self.context.dialect.mark_to_object(self.source_schema)}.{self.context.dialect.mark_to_object(self.source_table)} where {self.context.dialect.mark_to_object("ID")}=1''')
            data = self.context.get_table_count(schema=self.source_schema, table=self.source_table)
            assert data == 0
        except Exception as ex:
            ConsoleLogger().exception(ex)
            raise
        finally:
            self.context.drop_table(
                schema=self.source_schema,
                table=self.source_table,
            )

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

            self.context.create_table(schema=self.source_schema, table=self.source_table, columns=self.source_columns)
            self.context.execute(
                f'''insert into {self.context.dialect.mark_to_object(self.source_schema)}.{self.context.dialect.mark_to_object(self.source_table)} values(1,'test')''')
            TABLE_SPEC = [column.Name for column in self.source_columns]

            columns = [Column(n) for n in TABLE_SPEC]
            table = Table(self.source_table, MetaData(), schema=self.source_schema, *columns)
            from sqlalchemy.orm import sessionmaker, Session
            _SessionFactory = sessionmaker(bind=engine)
            session = _SessionFactory()

            qu = table.select().order_by(table.c.ID).limit(1).offset(0)
            res = session.execute(qu)
            result = list(res)
            session.commit()
            assert result[0][0] == 1
        except Exception as ex:
            ConsoleLogger().exception(ex)
            raise
        finally:
            self.context.drop_table(
                schema=self.source_schema,
                table=self.source_table,
            )

    def test_iterator(self):
        try:
            total_data_count = 130
            limit = 50
            TestSqlUtils.prepare_test_data_with_info(
                connection=self.connection,
                schema=self.source_schema,
                table=self.source_table,
                columns=self.source_columns,
                data_count=total_data_count
            )
            iterator = self.context.get_iterator(
                schema=self.source_schema,
                table=self.source_table,
                columns=self.source_columns,
                limit=limit
            )
            target_context = SqlProvider().get_context_by_config(self.connection)

            try:
                target_context.create_table(schema=self.target_schema, table=self.target_table,
                                            columns=self.target_columns)

                for results in iterator:
                    column_names = [c.Name for c in self.target_columns]
                    prepared_data = target_context.prepare_insert_row(results, column_names)
                    target_query = target_context.get_target_query(
                        schema=self.target_schema,
                        table=self.target_table,
                        query=None,
                        target_columns=column_names,
                        source_columns=column_names,
                        source_column_count=len(prepared_data[0])
                    )
                    target_context.execute_many(target_query, prepared_data)
            except Exception as ex:
                ConsoleLogger().exception(ex)
                raise
            finally:
                target_count = target_context.get_table_count(
                    schema=self.target_schema,
                    table=self.target_table
                )
                group_count = target_context.get_count_for_query(
                    f'''SELECT {target_context.dialect.mark_to_object("ID")} FROM  {target_context.dialect.mark_to_object(self.target_schema)}.{target_context.dialect.mark_to_object(self.target_table)} GROUP BY {target_context.dialect.mark_to_object("ID")} HAVING count(1)>1''')
                target_context.drop_table(
                    schema=self.target_schema,
                    table=self.target_table
                )
                target_context.connector.disconnect()
                assert group_count == 0
                assert total_data_count == target_count
        except Exception as ex:
            ConsoleLogger().exception(ex)
            raise
        finally:
            self.context.drop_table(
                schema=self.source_schema,
                table=self.source_table,
            )
