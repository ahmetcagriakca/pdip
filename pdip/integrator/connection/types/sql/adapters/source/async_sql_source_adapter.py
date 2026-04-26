from injector import inject

from pdip.integrator.connection.base import AsyncConnectionSourceAdapter
from pdip.integrator.connection.domain.enums import ConnectorTypes
from pdip.integrator.connection.types.sql.base.async_sql_dialect import (
    async_dialect_for,
)
from pdip.integrator.integration.domain.base import IntegrationBase


class AsyncSqlSourceAdapter(AsyncConnectionSourceAdapter):
    """Async source adapter for the SQL connector family
    (ADR-0032 §3 + §4 follow-up (a-3)).

    Per-driver behaviour (identifier quoting, paging clause) is
    delegated to :func:`async_dialect_for`; this adapter only
    owns the orchestration: open connector → render dialect-aware
    SELECT → drive ``fetch_count`` / ``fetch_all`` → close
    connector.
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
        cursor support is a future optimisation slice; the
        in-memory chunk preserves the sync sibling's batch-iteration
        contract that the ``SingleProcessIntegrationExecute``
        strategy reads via ``for results in iterator:``."""
        config = integration.SourceConnections.Sql.Connection
        connector = self._connector_for(config)
        dialect = async_dialect_for(config)
        try:
            await connector.connect()
            query = self._select_query_for(integration, dialect)
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
        """Per-dialect paging: ``LIMIT (end - start) OFFSET start``
        for Postgres / MySQL; ``OFFSET start ROWS FETCH NEXT
        (end - start) ROWS ONLY`` for MSSQL / Oracle 12c+. The
        ANSI form requires the source query to carry an
        ``ORDER BY`` clause for a deterministic page — when the
        descriptor's ``Sql.Query`` is empty and the integration
        has no column ordering, callers driving MSSQL / Oracle
        paging must supply an explicit query."""
        config = integration.SourceConnections.Sql.Connection
        connector = self._connector_for(config)
        dialect = async_dialect_for(config)
        try:
            await connector.connect()
            base_query = self._select_query_for(integration, dialect)
            paged_query = dialect.paging_clause(base_query, start, end)
            return await connector.fetch_all(paged_query)
        finally:
            await connector.disconnect()

    @staticmethod
    def _select_query_for(integration, dialect):
        """Return either the explicit ``Sql.Query`` from the
        descriptor, or a dialect-quoted ``SELECT`` for the named
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
                dialect.quote_identifier(c.Name) for c in columns
            )
        else:
            column_list = "*"
        return (
            f"SELECT {column_list} FROM "
            f"{dialect.quote_table(schema, table)}"
        )

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
