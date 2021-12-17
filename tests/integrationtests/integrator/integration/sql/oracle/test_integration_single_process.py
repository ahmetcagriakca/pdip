from random import randint
from unittest import TestCase

from pdip.base import Pdi
from pdip.integrator.connection.domain.authentication.basic import BasicAuthentication
from pdip.integrator.connection.domain.enums import ConnectorTypes, ConnectionTypes
from pdip.integrator.connection.domain.server.base import Server
from pdip.integrator.connection.domain.sql import SqlConnectionConfiguration
from pdip.integrator.connection.types.sql.base import SqlProvider
from pdip.integrator.integration.domain.base import IntegrationBase, IntegrationConnectionBase, \
    IntegrationConnectionSqlBase
from pdip.integrator.operation.base import OperationExecution
from pdip.integrator.operation.domain.operation import OperationIntegrationBase, OperationBase
from pdip.logging.loggers.console import ConsoleLogger


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
                ConnectionType=ConnectionTypes.Database,
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
            context = SqlProvider().get_context_by_config(connection)
            test_data = []
            for index, i in enumerate(range(100000)):
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

            operation = OperationBase()
            operation.Integrations = []
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
            integration = OperationIntegrationBase(
                Order=1,
                Limit=0,
                ProcessCount=0,
                Integration=IntegrationBase(
                    TargetConnections=IntegrationConnectionBase(
                        ConnectionName=connection.Name,
                        ConnectionType=connection.ConnectionType,
                        Sql=IntegrationConnectionSqlBase(
                            Connection=connection,
                            Query=query
                        )
                    )
                )
            )
            operation.Integrations.append(integration)

            integration = OperationIntegrationBase(
                Order=2,
                Limit=10000,
                ProcessCount=0,
                Integration=IntegrationBase(
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
            )
            operation.Integrations.append(integration)

            integration = OperationIntegrationBase(
                Order=3,
                Limit=0,
                ProcessCount=0,
                Integration=IntegrationBase(
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
            operation.Integrations.append(integration)
            self.pdi.get(OperationExecution).start(operation)
        except Exception as ex:
            self.pdi.get(ConsoleLogger).exception(ex)
            raise
        finally:
            try:
                SqlProvider().get_context_by_config(connection).execute('''DROP TABLE test_pdi.test_source''')
            except:
                pass
