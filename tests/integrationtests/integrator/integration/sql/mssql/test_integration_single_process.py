from unittest import TestCase

from pdip.base import Pdi
from pdip.integrator.base.integrator import Integrator
from pdip.integrator.connection.domain.authentication.basic import ConnectionBasicAuthentication
from pdip.integrator.connection.domain.enums import ConnectorTypes, ConnectionTypes
from pdip.integrator.connection.domain.server.base import ConnectionServer
from pdip.integrator.connection.domain.types.sql.configuration.base import SqlConnectionConfiguration
from pdip.integrator.connection.types.sql.base import SqlProvider
from pdip.integrator.integration.domain.base import IntegrationBase, IntegrationConnectionBase
from pdip.integrator.connection.domain.types.sql.base.sql import ConnectionSqlBase
from pdip.integrator.operation.domain.operation import OperationIntegrationBase, OperationBase
from pdip.logging.loggers.console import ConsoleLogger
from tests.integrationtests.integrator.integration.sql.utils import TestSqlUtils


class TestMssqlIntegration(TestCase):
    def setUp(self):
        try:
            self.pdi = Pdi()
            self.logger = self.pdi.get(ConsoleLogger)
        except:
            self.tearDown()
            raise

    def tearDown(self):
        if hasattr(self, 'pdi') and self.pdi is not None:
            self.pdi.cleanup()
            del self.pdi
            del self.logger
        return super().tearDown()

    def test_integration(self):
        try:
            connection = SqlConnectionConfiguration(
                Name='TestConnection',
                ConnectionType=ConnectionTypes.Sql,
                ConnectorType=ConnectorTypes.MSSQL,
                Server=ConnectionServer(
                    Host='localhost,1433'
                ),
                Database='test_pdi',
                BasicAuthentication=ConnectionBasicAuthentication(
                    User='pdi',
                    Password='pdi!123456'
                )
            )
            TestSqlUtils.prepare_test_data(connection, data_count=1000000)
            query = '''IF NOT EXISTS (SELECT 0 
                       FROM INFORMATION_SCHEMA.TABLES 
                       WHERE TABLE_SCHEMA = 'test_pdi' 
                       AND TABLE_NAME = 'test_target')
            begin
            CREATE TABLE test_pdi.test_target (
                Id INT NULL,
                Name varchar(100) NULL
            )
            end'''
            operation = OperationBase(
                Name='TestOperation',
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
                                Sql=ConnectionSqlBase(
                                    Connection=connection,
                                    Query=query
                                )
                            )
                        )
                    ),
                    OperationIntegrationBase(
                        Name='TestIntegrationLoadData',
                        Order=2,
                        Limit=100000,
                        ProcessCount=0,
                        Integration=IntegrationBase(
                            SourceConnections=IntegrationConnectionBase(
                                ConnectionName=connection.Name,
                                ConnectionType=connection.ConnectionType,
                                Sql=ConnectionSqlBase(
                                    Connection=connection,
                                    Schema='test_pdi',
                                    ObjectName='test_source'
                                )
                            ),
                            TargetConnections=IntegrationConnectionBase(
                                ConnectionName=connection.Name,
                                ConnectionType=connection.ConnectionType,
                                Sql=ConnectionSqlBase(
                                    Connection=connection,
                                    Schema='test_pdi',
                                    ObjectName='test_target'
                                )
                            )
                        )
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
                                Sql=ConnectionSqlBase(
                                    Connection=connection,
                                    Query='DROP TABLE test_pdi.test_target'
                                )
                            )
                        )
                    )
                ]
            )
            integrator = self.pdi.get(Integrator)
            integrator.integrate(operation)

        except Exception as ex:
            self.logger.exception(ex)
            raise
        finally:
            try:
                SqlProvider().get_context_by_config(connection).execute('''DROP TABLE test_pdi.test_source''')
            except:
                pass
