from unittest import TestCase

from pdip.base import Pdi
from pdip.integrator.base import Integrator
from pdip.integrator.connection.domain.authentication.basic import ConnectionBasicAuthentication
from pdip.integrator.connection.domain.base import ConnectionColumnBase
from pdip.integrator.connection.domain.enums import ConnectorTypes, ConnectionTypes
from pdip.integrator.connection.domain.server.base import ConnectionServer
from pdip.integrator.connection.domain.types.sql.configuration.base import SqlConnectionConfiguration
from pdip.integrator.connection.types.sql.base import SqlProvider
from pdip.logging.loggers.console import ConsoleLogger
from tests.integrationtests.integrator.integration.sql.utils import TestSqlUtils


class TestOracleIntegration(TestCase):
    def setUp(self):
        try:
            self.pdi = Pdi()
            self.connection = SqlConnectionConfiguration(
                Name='TestConnection',
                ConnectionType=ConnectionTypes.Sql,
                ConnectorType=ConnectorTypes.ORACLE,
                Server=ConnectionServer(
                    Host='localhost',
                    Port=1521
                ),
                # Modern Oracle (12c+) is a CDB containing pluggable
                # databases (PDBs); the ``gvenzl/oracle-xe:21-*`` image
                # creates a PDB named after ``ORACLE_DATABASE`` and
                # creates ``APP_USER`` inside it. Connect via the PDB
                # service name rather than the legacy SID. See
                # tests/environments/oracle/ for the matching image
                # configuration.
                ServiceName='test_pdi',
                BasicAuthentication=ConnectionBasicAuthentication(
                    # Oracle treats ``user name == schema name``, so
                    # connecting as ``test_pdi`` lands writes under
                    # the ``TEST_PDI`` schema below. The fixture's
                    # APP_USER env in
                    # ``tests/environments/oracle/docker-compose.yml``
                    # creates this user inside the ``test_pdi`` PDB.
                    User='test_pdi',
                    Password='pdi!123456'
                )
            )
            self.source_schema = 'TEST_PDI'
            self.source_table = 'TEST_SOURCE'
            self.source_columns = [
                ConnectionColumnBase(Name='ID', Type='INT'),
                ConnectionColumnBase(Name='NAME', Type='varchar(100)'),
            ]
            self.target_schema = 'TEST_PDI'
            self.target_table = 'TEST_TARGET'
            self.target_columns = [
                ConnectionColumnBase(Name='ID', Type='INT'),
                ConnectionColumnBase(Name='NAME', Type='varchar(100)'),
            ]

        except Exception:
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
            except Exception:
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
            except Exception:
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
            except Exception:
                pass
