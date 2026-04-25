from typing import List

from injector import inject

from pdip.integrator.connection.base import AsyncConnectionTargetAdapter
from pdip.integrator.connection.domain.enums import ConnectorTypes
from pdip.integrator.integration.domain.base import IntegrationBase


class AsyncSqlTargetAdapter(AsyncConnectionTargetAdapter):
    """First-cut async target adapter (ADR-0032 §3 + §4 follow-up).

    Symmetric with :class:`AsyncSqlSourceAdapter` — provider/context
    abstraction is deferred. Postgres is the only wired backend in
    this build; other ``ConnectorTypes`` raise ``NotImplementedError``
    from :meth:`_connector_for` until their async siblings land.
    """

    @inject
    def __init__(self):
        pass

    async def clear_data(self, integration: IntegrationBase) -> int:
        # First-cut clear_data implementation for Postgres only via
        # ``TRUNCATE TABLE``. Other backends still raise
        # ``NotImplementedError`` from ``_connector_for`` because the
        # quoting (backticks for MySQL, brackets for MSSQL) and
        # commit semantics differ — they land per-driver as the
        # connectors mature. Postgres ``TRUNCATE`` returns no row
        # count, so we report ``0`` per the sync sibling's contract
        # (``truncate_affected_rowcount`` from ``SqlContext``).
        connector = self._connector_for(
            integration.TargetConnections.Sql.Connection
        )
        try:
            await connector.connect()
            schema = integration.TargetConnections.Sql.Schema
            table = integration.TargetConnections.Sql.ObjectName
            await connector.execute(
                f'TRUNCATE TABLE "{schema}"."{table}"'
            )
            return 0
        finally:
            await connector.disconnect()

    async def write_data(
            self, integration: IntegrationBase, source_data: List[any]
    ) -> int:
        """First-cut write_data: bulk-insert ``source_data`` into the
        configured target schema/table via ``executemany``. Column
        list is taken from the integration descriptor when present,
        otherwise inferred from the keys of the first source row
        (mirrors the sync sibling's ``SqlTargetAdapter.prepare_data``
        behaviour). Returns the row count actually shipped.

        Postgres uses asyncpg's ``$1, $2, ...`` placeholder style;
        the dialect-specific placeholder ladder for MySQL / MSSQL /
        Oracle lands per-driver in subsequent slices."""
        if not source_data:
            return 0
        config = integration.TargetConnections.Sql.Connection
        connector = self._connector_for(config)
        try:
            await connector.connect()
            schema = integration.TargetConnections.Sql.Schema
            table = integration.TargetConnections.Sql.ObjectName
            column_names = self._target_column_names(
                integration, source_data
            )
            column_list = ", ".join(f'"{n}"' for n in column_names)
            placeholders = ", ".join(
                f"${i + 1}" for i in range(len(column_names))
            )
            query = (
                f'INSERT INTO "{schema}"."{table}" '
                f'({column_list}) VALUES ({placeholders})'
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
