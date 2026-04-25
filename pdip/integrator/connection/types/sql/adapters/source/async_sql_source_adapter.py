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
        """First-cut iterator: fetches the full result set into
        memory and chunks into batches of ``limit`` rows. Streaming
        cursor support (asyncpg's per-transaction ``cursor()``) is
        a future optimisation slice; the in-memory chunk preserves
        the sync sibling's batch-iteration contract that the
        ``SingleProcessIntegrationExecute`` strategy reads via
        ``for results in iterator:``."""
        config = integration.SourceConnections.Sql.Connection
        connector = self._connector_for(config)
        try:
            await connector.connect()
            query = self._select_query_for(integration)
            rows = await connector.fetch_all(query)
            if limit is None or limit <= 0:
                # ``limit`` of None / 0 means "no chunking": the
                # whole result set is one batch.
                return [rows] if rows else []
            return [rows[i:i + limit] for i in range(0, len(rows), limit)]
        finally:
            await connector.disconnect()

    async def get_source_data_with_paging(
            self, integration: IntegrationBase, start: int, end: int
    ):
        """First-cut paging: ``LIMIT (end - start) OFFSET start`` on
        the dialect's standard SELECT. Postgres / MySQL accept the
        SQL-standard form directly; MSSQL needs ``OFFSET ... ROWS
        FETCH NEXT ... ROWS ONLY`` which lands per-driver as the
        target dialects' adapters mature."""
        config = integration.SourceConnections.Sql.Connection
        connector = self._connector_for(config)
        try:
            await connector.connect()
            base_query = self._select_query_for(integration)
            paged_query = (
                f"{base_query} LIMIT {end - start} OFFSET {start}"
            )
            return await connector.fetch_all(paged_query)
        finally:
            await connector.disconnect()

    @staticmethod
    def _select_query_for(integration):
        """Return either the explicit ``Sql.Query`` from the
        descriptor, or a generated ``SELECT`` for the named
        ``Schema.ObjectName`` with the documented column list (or
        ``*`` when no columns are listed). Mirrors the sync
        sibling's ``SqlSourceAdapter.get_source_data`` shape."""
        if integration.SourceConnections.Sql.Query:
            return integration.SourceConnections.Sql.Query
        schema = integration.SourceConnections.Sql.Schema
        table = integration.SourceConnections.Sql.ObjectName
        columns = integration.SourceConnections.Columns
        if columns:
            column_list = ", ".join(
                f'"{c.Name}"' for c in columns
            )
        else:
            column_list = "*"
        return f'SELECT {column_list} FROM "{schema}"."{table}"'

    @staticmethod
    def _connector_for(config):
        if config.ConnectorType == ConnectorTypes.POSTGRESQL:
            from pdip.integrator.connection.types.sql.connectors.postgresql.async_postgresql_connector import (
                AsyncPostgresqlConnector,
            )
            return AsyncPostgresqlConnector(config=config)
        if config.ConnectorType == ConnectorTypes.MYSQL:
            from pdip.integrator.connection.types.sql.connectors.mysql.async_mysql_connector import (
                AsyncMysqlConnector,
            )
            return AsyncMysqlConnector(config=config)
        if config.ConnectorType == ConnectorTypes.MSSQL:
            from pdip.integrator.connection.types.sql.connectors.mssql.async_mssql_connector import (
                AsyncMssqlConnector,
            )
            return AsyncMssqlConnector(config=config)
        if config.ConnectorType == ConnectorTypes.ORACLE:
            from pdip.integrator.connection.types.sql.connectors.oracle.async_oracle_connector import (
                AsyncOracleConnector,
            )
            return AsyncOracleConnector(config=config)
        raise NotImplementedError(
            f"async connector for {config.ConnectorType.name} is not "
            f"yet wired in this build (see ADR-0032 follow-ups)"
        )
