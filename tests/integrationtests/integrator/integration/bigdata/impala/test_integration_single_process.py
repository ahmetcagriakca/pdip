from unittest import TestCase

from pdip.base import Pdi
from pdip.integrator.connection.domain.authentication.basic import BasicAuthentication
from pdip.integrator.connection.domain.authentication.mechanism import MechanismTypes
from pdip.integrator.connection.domain.bigdata import BigDataConnectionConfiguration
from pdip.integrator.connection.domain.enums import ConnectorTypes, ConnectionTypes
from pdip.integrator.connection.domain.server.base import Server
from pdip.integrator.integration.domain.base import IntegrationBase, IntegrationConnectionBase
from pdip.integrator.integration.domain.base.integration import IntegrationConnectionBigDataBase
from pdip.integrator.operation.base import OperationExecution
from pdip.integrator.operation.domain.operation import OperationIntegrationBase, OperationBase
from pdip.logging.loggers.console import ConsoleLogger


class TestImpalaIntegration(TestCase):
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
            connection = BigDataConnectionConfiguration(
                Name='TestConnection',
                ConnectionType=ConnectionTypes.BigData,
                ConnectorType=ConnectorTypes.Impala,
                AuthenticationMechanismType=MechanismTypes.UserNamePassword,
                Server=Server(
                    Host='localhost',
                    Port=21050
                ),
                Database='default',
                BasicAuthentication=BasicAuthentication(
                    User='pdi',
                    Password='pdi!123456'
                )
            )

            operation = OperationBase()
            operation.Integrations = []

            integration = OperationIntegrationBase(
                Order=1,
                Limit=10000,
                ProcessCount=0,
                Integration=IntegrationBase(
                    SourceConnections=IntegrationConnectionBase(
                        ConnectionName=connection.Name,
                        ConnectionType=connection.ConnectionType,
                        BigData=IntegrationConnectionBigDataBase(
                            Connection=connection,
                            Schema='default',
                            ObjectName='test_source',
                            Query=None
                        )
                    ),
                    TargetConnections=IntegrationConnectionBase(
                        ConnectionName=connection.Name,
                        ConnectionType=connection.ConnectionType,
                        BigData=IntegrationConnectionBigDataBase(
                            Connection=connection,
                            Schema='default',
                            ObjectName='test_target',
                            Query=None
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
            pass
