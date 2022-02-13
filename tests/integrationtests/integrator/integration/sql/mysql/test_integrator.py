from unittest import TestCase

from pdip.base import Pdi
from pdip.integrator.base import Integrator
from pdip.integrator.connection.domain.authentication.basic import ConnectionBasicAuthentication
from pdip.integrator.connection.domain.base import ConnectionColumnBase
from pdip.integrator.connection.domain.enums import ConnectionTypes, ConnectorTypes
from pdip.integrator.connection.domain.server.base import ConnectionServer
from pdip.integrator.connection.domain.types.sql.configuration.base import SqlConnectionConfiguration
from pdip.integrator.connection.types.sql.base import SqlProvider
from pdip.logging.loggers.console import ConsoleLogger
from tests.integrationtests.integrator.integration.sql.utils import TestSqlUtils


class TestMysqlIntegration(TestCase):
    def setUp(self):
        try:
            self.pdi = Pdi()
            self.connection = SqlConnectionConfiguration(
                Name='TestConnection',
                ConnectionType=ConnectionTypes.Sql,
                ConnectorType=ConnectorTypes.MYSQL,
                Server=ConnectionServer(
                    Host='localhost',
                    Port=3306
                ),
                Database='test_pdi',
                BasicAuthentication=ConnectionBasicAuthentication(
                    User='pdi',
                    Password='pdi!123456'
                )
            )
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

        except:
            self.tearDown()
            raise

    def tearDown(self):
        if hasattr(self, 'pdi') and self.pdi is not None:
            self.pdi.cleanup()
            del self.pdi
        return super().tearDown()

    def test_integration_limit_off(self):
        try:
            limit = 0
            process_count = 0
            test_data_count = 10000

            TestSqlUtils.prepare_test_data_with_info(
                connection=self.connection,
                schema=self.source_schema,
                table=self.source_table,
                columns=self.source_columns,
                data_count=test_data_count
            )
            operation = TestSqlUtils.get_operation(
                connection=self.connection,
                source_schema=self.source_schema,
                source_table=self.source_table,
                target_schema=self.target_schema,
                target_table=self.target_table,
                target_columns=self.target_columns,
                limit=limit,
                process_count=process_count
            )
            self.pdi \
                .get(Integrator) \
                .integrate(operation)
        except Exception as ex:
            self.pdi \
                .get(ConsoleLogger) \
                .exception(ex)
            raise
        finally:
            try:
                self.pdi \
                    .get(SqlProvider) \
                    .get_context_by_config(self.connection) \
                    .drop_table(schema=self.source_schema,
                                table=self.source_table
                                )
            except:
                pass

    def test_integration_single_process(self):
        try:
            limit = 1000
            process_count = 0
            test_data_count = 10000

            TestSqlUtils.prepare_test_data_with_info(
                connection=self.connection,
                schema=self.source_schema,
                table=self.source_table,
                columns=self.source_columns,
                data_count=test_data_count
            )
            operation = TestSqlUtils.get_operation(
                connection=self.connection,
                source_schema=self.source_schema,
                source_table=self.source_table,
                target_schema=self.target_schema,
                target_table=self.target_table,
                target_columns=self.target_columns,
                limit=limit,
                process_count=process_count
            )
            self.pdi \
                .get(Integrator) \
                .integrate(operation)
        except Exception as ex:
            self.pdi \
                .get(ConsoleLogger) \
                .exception(ex)
            raise
        finally:
            try:
                self.pdi \
                    .get(SqlProvider) \
                    .get_context_by_config(self.connection) \
                    .drop_table(schema=self.source_schema,
                                table=self.source_table
                                )
            except:
                pass

    def test_integration_parallel(self):
        try:
            limit = 10000
            process_count = 5
            test_data_count = 500000

            TestSqlUtils.prepare_test_data_with_info(
                connection=self.connection,
                schema=self.source_schema,
                table=self.source_table,
                columns=self.source_columns,
                data_count=test_data_count
            )
            operation = TestSqlUtils.get_operation(
                connection=self.connection,
                source_schema=self.source_schema,
                source_table=self.source_table,
                target_schema=self.target_schema,
                target_table=self.target_table,
                target_columns=self.target_columns,
                limit=limit,
                process_count=process_count
            )
            self.pdi \
                .get(Integrator) \
                .integrate(operation)
        except Exception as ex:
            self.pdi \
                .get(ConsoleLogger) \
                .exception(ex)
            raise
        finally:
            try:
                self.pdi \
                    .get(SqlProvider) \
                    .get_context_by_config(self.connection) \
                    .drop_table(schema=self.source_schema,
                                table=self.source_table
                                )
            except:
                pass
