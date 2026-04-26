from unittest import TestCase

from pdip.base import Pdi
from pdip.integrator.base import Integrator
from pdip.integrator.connection.domain.authentication.mechanism import MechanismTypes
from pdip.integrator.connection.domain.base import ConnectionColumnBase
from pdip.integrator.connection.domain.enums import ConnectionTypes, ConnectorTypes
from pdip.integrator.connection.domain.server.base import ConnectionServer
from pdip.integrator.connection.domain.types.bigdata.configuration.base import (
    BigDataConnectionConfiguration,
)
from pdip.integrator.connection.types.bigdata.base import BigDataProvider
from pdip.logging.loggers.console import ConsoleLogger
from tests.integrationtests.integrator.integration.bigdata.utils import TestBigDataUtils


class TestImpalaIntegrationLimitOff(TestCase):
    """Limit-off (whole-table) integration smoke against the Apache
    Impala fixture under ``tests/environments/bigdata/impala/``
    (ADR-0030 Stage 1). Identical wiring to the single-process
    test but with ``Limit = 0`` so the integrator pulls the source
    table in a single page rather than chunking through paged
    reads.
    """

    def setUp(self):
        try:
            self.pdi = Pdi()
            self.connection = BigDataConnectionConfiguration(
                Name='TestConnection',
                ConnectionType=ConnectionTypes.BigData,
                ConnectorType=ConnectorTypes.Impala,
                AuthenticationMechanismType=MechanismTypes.NoAuthentication,
                Server=ConnectionServer(
                    Host='localhost',
                    Port=21050,
                ),
                Database='default',
            )
            self.source_schema = 'default'
            self.source_table = 'test_source'
            self.source_columns = [
                ConnectionColumnBase(Name='ID', Type='INT'),
                ConnectionColumnBase(Name='NAME', Type='STRING'),
            ]
            self.target_schema = 'default'
            self.target_table = 'test_target'
            self.target_columns = [
                ConnectionColumnBase(Name='ID', Type='INT'),
                ConnectionColumnBase(Name='NAME', Type='STRING'),
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

            TestBigDataUtils.prepare_test_data_with_info(
                connection=self.connection,
                schema=self.source_schema,
                table=self.source_table,
                columns=self.source_columns,
                data_count=test_data_count,
            )
            operation = TestBigDataUtils.get_operation(
                connection=self.connection,
                source_schema=self.source_schema,
                source_table=self.source_table,
                target_schema=self.target_schema,
                target_table=self.target_table,
                target_columns=self.target_columns,
                limit=limit,
                process_count=process_count,
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
                    .get(BigDataProvider) \
                    .get_context_by_config(self.connection) \
                    .drop_table(schema=self.source_schema,
                                table=self.source_table)
            except Exception:
                pass
