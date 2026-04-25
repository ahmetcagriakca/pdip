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
        # Truncation needs per-dialect quoting and TRUNCATE vs
        # DELETE-ALL semantics; this is the next async-target slice
        # once a second backend lands. Until then, callers get a
        # deterministic ``NotImplementedError``.
        raise NotImplementedError(
            "async clear_data is queued for a follow-up slice "
            "(ADR-0032)"
        )

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
        raise NotImplementedError(
            f"async connector for {config.ConnectorType.name} is not "
            f"yet wired in this build (see ADR-0032 follow-ups)"
        )
