from injector import inject

from pdip.integrator.connection.base import AsyncConnectionSourceAdapter
from pdip.integrator.connection.domain.enums import ConnectorTypes
from pdip.integrator.integration.domain.base import IntegrationBase


class AsyncSqlSourceAdapter(AsyncConnectionSourceAdapter):
    """First-cut async source adapter (ADR-0032 §3 + §4 follow-up).

    The full provider/context chain that the sync :class:`SqlSourceAdapter`
    rides on is intentionally NOT mirrored yet — the first
    implementation reads the connection config straight from the
    integration descriptor and instantiates the matching async
    connector inline. Subsequent connectors (MySQL via aiomysql,
    MSSQL via aioodbc, Oracle via oracledb async) follow the same
    pattern; the abstraction layer is a deliberate later refactor.

    Postgres is the only wired backend in this build. Other
    ``ConnectorTypes`` raise :class:`NotImplementedError` from
    :meth:`_connector_for` until their async siblings land.
    """

    @inject
    def __init__(self):
        # No DI deps in the first cut. Future: an
        # ``AsyncSqlConnectorFactory`` parallel to the sync
        # ``SqlConnectorFactory`` lands here as a constructor
        # argument.
        pass

    async def get_source_data_count(
            self, integration: IntegrationBase
    ) -> int:
        connector = self._connector_for(
            integration.SourceConnections.Sql.Connection
        )
        try:
            await connector.connect()
            return await connector.fetch_count(
                schema=integration.SourceConnections.Sql.Schema,
                table=integration.SourceConnections.Sql.ObjectName,
            )
        finally:
            await connector.disconnect()

    async def get_iterator(self, integration: IntegrationBase, limit: int):
        # Iterator semantics require streaming cursor support per
        # backend; this is the next implementation slice once a
        # second connector lands. Raising ``NotImplementedError`` is
        # the documented interim contract per ADR-0032 §3.
        raise NotImplementedError(
            "async iterator support is queued for a follow-up slice "
            "(ADR-0032)"
        )

    async def get_source_data_with_paging(
            self, integration: IntegrationBase, start: int, end: int
    ):
        raise NotImplementedError(
            "async paging support is queued for a follow-up slice "
            "(ADR-0032)"
        )

    @staticmethod
    def _connector_for(config):
        if config.ConnectorType == ConnectorTypes.POSTGRESQL:
            from pdip.integrator.connection.types.sql.connectors.postgresql.async_postgresql_connector import (
                AsyncPostgresqlConnector,
            )
            return AsyncPostgresqlConnector(config=config)
        raise NotImplementedError(
            f"async connector for {config.ConnectorType.name} is not "
            f"yet wired in this build (see ADR-0032 follow-ups)"
        )
