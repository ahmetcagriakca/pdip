from unittest import TestCase

from pdip.base import Pdi
from pdip.integrator.base import Integrator
from pdip.integrator.connection.domain.authentication.basic import BasicAuthentication
from pdip.integrator.connection.domain.enums import ConnectorTypes, ConnectionTypes
from pdip.integrator.connection.domain.server.base import Server
from pdip.integrator.connection.domain.sql import SqlConnectionConfiguration
from pdip.integrator.connection.types.sql.base import SqlProvider
from pdip.integrator.integration.domain.base import IntegrationBase, IntegrationConnectionBase, \
    IntegrationConnectionSqlBase
from pdip.integrator.operation.domain.operation import OperationIntegrationBase, OperationBase
from pdip.logging.loggers.console import ConsoleLogger
from tests.integrationtests.integrator.integration.sql.utils import TestSqlUtils


class TestOracleIntegration(TestCase):
    def setUp(self):
        try:
            self.pdi = Pdi()
        except:
            self.tearDown()
            raise

    def tearDown(self):
        if hasattr(self, 'pdi') and self.pdi is not None:
            self.pdi.cleanup()
            del self.pdi
        return super().tearDown()

    def test_integration(self):
        try:
            connection = SqlConnectionConfiguration(
                Name='TestConnection',
                ConnectionType=ConnectionTypes.Sql,
                ConnectorType=ConnectorTypes.ORACLE,
                Server=Server(
                    Host='localhost',
                    Port=1521
                ),
                Sid='xe',
                BasicAuthentication=BasicAuthentication(
                    User='pdi',
                    Password='pdi!123456'
                )
            )
            TestSqlUtils.prepare_test_data(connection, data_count=1000000)
            query = '''declare
v_sql LONG;
begin

v_sql:='CREATE TABLE test_pdi.test_target (
    Id INT NULL,
    Name varchar(100) NULL
)';
execute immediate v_sql;

EXCEPTION
    WHEN OTHERS THEN
      IF SQLCODE = -955 THEN
        NULL; -- suppresses ORA-00955 exception
      ELSE
         RAISE;
      END IF;
END;
'''
            operation = OperationBase(
                Name='TestOperation',
                Integrations=[
                    OperationIntegrationBase(
                        Order=1,
                        Limit=0,
                        ProcessCount=0,
                        Integration=IntegrationBase(
                            Name='TestIntegrationCreateTable',
                            TargetConnections=IntegrationConnectionBase(
                                ConnectionName=connection.Name,
                                ConnectionType=connection.ConnectionType,
                                Sql=IntegrationConnectionSqlBase(
                                    Connection=connection,
                                    Query=query
                                )
                            )
                        )
                    ),
                    OperationIntegrationBase(
                        Order=2,
                        Limit=50000,
                        ProcessCount=5,
                        Integration=IntegrationBase(
                            Name='TestIntegrationLoadData',
                            SourceConnections=IntegrationConnectionBase(
                                ConnectionName=connection.Name,
                                ConnectionType=connection.ConnectionType,
                                Sql=IntegrationConnectionSqlBase(
                                    Connection=connection,
                                    Schema='test_pdi',
                                    ObjectName='test_source'
                                )
                            ),
                            TargetConnections=IntegrationConnectionBase(
                                ConnectionName=connection.Name,
                                ConnectionType=connection.ConnectionType,
                                Sql=IntegrationConnectionSqlBase(
                                    Connection=connection,
                                    Schema='test_pdi',
                                    ObjectName='test_target'
                                )
                            )
                        )
                    ),
                    OperationIntegrationBase(
                        Order=3,
                        Limit=0,
                        ProcessCount=0,
                        Integration=IntegrationBase(
                            Name='TestIntegrationDropTable',
                            TargetConnections=IntegrationConnectionBase(
                                ConnectionName=connection.Name,
                                ConnectionType=connection.ConnectionType,
                                Sql=IntegrationConnectionSqlBase(
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
            self.pdi.get(ConsoleLogger).exception(ex)
            raise
        finally:
            try:
                SqlProvider().get_context_by_config(connection).execute('''DROP TABLE test_pdi.test_source''')
            except:
                pass
