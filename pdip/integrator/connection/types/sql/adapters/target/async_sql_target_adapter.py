from typing import List

from injector import inject

from pdip.integrator.connection.base import AsyncConnectionTargetAdapter
from pdip.integrator.connection.domain.enums import ConnectorTypes
from pdip.integrator.connection.types.sql.base.async_sql_dialect import (
    async_dialect_for,
)
from pdip.integrator.integration.domain.base import IntegrationBase


class AsyncSqlTargetAdapter(AsyncConnectionTargetAdapter):
    """Async target adapter for the SQL connector family
    (ADR-0032 §3 + §4 follow-up (a-3)).

    Per-driver behaviour (placeholder ladder, identifier quoting,
    paging clause, TRUNCATE wording) is delegated to
    :func:`async_dialect_for`; this adapter only owns the
    orchestration: open connector → render dialect-aware SQL →
    drive ``executemany`` / ``execute`` → close connector.
    """

    @inject
    def __init__(self):
        pass

    async def clear_data(self, integration: IntegrationBase) -> int:
        # ``TRUNCATE TABLE`` is portable across all four async
        # backends, but the identifier quoting differs (``"`` for
        # Postgres / Oracle, backtick for MySQL, ``[ ]`` for MSSQL);
        # the dialect renders the right form. Postgres / MSSQL
        # ``TRUNCATE`` returns no row count so we report ``0`` per
        # the sync sibling's contract (``truncate_affected_rowcount``
        # from ``SqlContext``).
        config = integration.TargetConnections.Sql.Connection
        connector = self._connector_for(config)
        dialect = async_dialect_for(config)
        try:
            await connector.connect()
            schema = integration.TargetConnections.Sql.Schema
            table = integration.TargetConnections.Sql.ObjectName
            await connector.execute(dialect.truncate_query(schema, table))
            return 0
        finally:
            await connector.disconnect()

    async def write_data(
            self, integration: IntegrationBase, source_data: List[any]
    ) -> int:
        """Bulk-insert ``source_data`` into the configured target
        schema / table via ``executemany``. Column list is taken
        from the integration descriptor when present, otherwise
        inferred from the keys of the first source row (mirrors
        the sync sibling's ``SqlTargetAdapter.prepare_data``
        behaviour). Returns the row count actually shipped.

        Each backend's placeholder syntax differs (asyncpg ``$N``,
        aiomysql ``%s``, aioodbc ``?``, oracledb ``:N``); the
        dialect renders the matching ladder for the column count
        and the connector's ``executemany`` does the bind."""
        if not source_data:
            return 0
        config = integration.TargetConnections.Sql.Connection
        connector = self._connector_for(config)
        dialect = async_dialect_for(config)
        try:
            await connector.connect()
            schema = integration.TargetConnections.Sql.Schema
            table = integration.TargetConnections.Sql.ObjectName
            column_names = self._target_column_names(
                integration, source_data
            )
            column_list = ", ".join(
                dialect.quote_identifier(n) for n in column_names
            )
            placeholders = dialect.insert_placeholders(len(column_names))
            query = (
                f"INSERT INTO {dialect.quote_table(schema, table)} "
                f"({column_list}) VALUES ({placeholders})"
            )
            rows = [
                tuple(self._extract(row, name, idx)
                      for idx, name in enumerate(column_names))
                for row in source_data
            ]
            await connector.executemany(query, rows)
            return len(rows)
        finally:
            await connector.disconnect()

    async def do_target_operation(
            self, integration: IntegrationBase
    ) -> int:
        """Orchestrates the per-integration target setup. Today this
        means: when ``integration.IsTargetTruncate`` is set, call
        :meth:`clear_data` and return its row count; otherwise
        return 0 and let the strategy drive ``write_data`` directly.
        Mirrors the sync sibling's pre-write hook shape."""
        if getattr(integration, "IsTargetTruncate", None):
            return await self.clear_data(integration)
        return 0

    @staticmethod
    def _target_column_names(integration, source_data):
        columns = integration.TargetConnections.Columns
        if columns:
            return [c.Name for c in columns]
        first = source_data[0]
        if isinstance(first, dict):
            return list(first.keys())
        # Positional rows (tuple / list) without a column descriptor
        # cannot be safely matched to target columns. The sync
        # sibling raises in this branch too.
        raise ValueError(
            "AsyncSqlTargetAdapter.write_data requires either "
            "integration.TargetConnections.Columns or dict-shaped "
            "source rows so columns can be inferred"
        )

    @staticmethod
    def _extract(row, name, index):
        if isinstance(row, dict):
            return row[name]
        return row[index]

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
