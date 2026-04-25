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
        raise NotImplementedError(
            "async write_data is queued for a follow-up slice "
            "(ADR-0032)"
        )

    async def do_target_operation(
            self, integration: IntegrationBase
    ) -> int:
        raise NotImplementedError(
            "async do_target_operation is queued for a follow-up "
            "slice (ADR-0032)"
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
