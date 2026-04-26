"""Async SQL dialect helper (ADR-0032 §3 follow-up (a-3)).

The sync :class:`SqlDialect` rides on sqlalchemy's inspector and
covers a much wider surface (CRUD, schema inspection, table
discovery). The async sibling needs only enough to render the
four call sites that :class:`AsyncSqlSourceAdapter` and
:class:`AsyncSqlTargetAdapter` drive: identifier quoting, INSERT
placeholder ladder, paging clause, and the TRUNCATE statement.

Each backend's placeholder syntax differs (asyncpg ``$N``,
aiomysql ``%s``, aioodbc ``?``, oracledb ``:N``); identifier
quoting differs (``"`` for Postgres / Oracle, backtick for
MySQL, square brackets for MSSQL); paging diverges between the
LIMIT/OFFSET dialects (Postgres / MySQL) and the ANSI
``OFFSET ... FETCH NEXT`` form (MSSQL / Oracle 12c+).
"""

from abc import ABC, abstractmethod

from pdip.integrator.connection.domain.enums import ConnectorTypes


class AsyncSqlDialect(ABC):
    @abstractmethod
    def quote_identifier(self, name: str) -> str:
        """Wrap ``name`` in the dialect's identifier quote chars."""

    @abstractmethod
    def insert_placeholders(self, count: int) -> str:
        """Render the ``VALUES`` placeholder list for ``executemany``,
        e.g. ``$1, $2, $3`` for asyncpg or ``?, ?, ?`` for aioodbc."""

    def quote_table(self, schema: str, table: str) -> str:
        return (
            f"{self.quote_identifier(schema)}."
            f"{self.quote_identifier(table)}"
        )

    def paging_clause(self, base_query: str, start: int, end: int) -> str:
        """Default LIMIT/OFFSET form (Postgres + MySQL). MSSQL +
        Oracle override to ANSI ``OFFSET ... FETCH NEXT``."""
        return f"{base_query} LIMIT {end - start} OFFSET {start}"

    def truncate_query(self, schema: str, table: str) -> str:
        return f"TRUNCATE TABLE {self.quote_table(schema, table)}"


class AsyncPostgresqlDialect(AsyncSqlDialect):
    def quote_identifier(self, name: str) -> str:
        return f'"{name}"'

    def insert_placeholders(self, count: int) -> str:
        return ", ".join(f"${i + 1}" for i in range(count))


class AsyncMysqlDialect(AsyncSqlDialect):
    def quote_identifier(self, name: str) -> str:
        return f"`{name}`"

    def insert_placeholders(self, count: int) -> str:
        return ", ".join("%s" for _ in range(count))


class AsyncMssqlDialect(AsyncSqlDialect):
    def quote_identifier(self, name: str) -> str:
        return f"[{name}]"

    def insert_placeholders(self, count: int) -> str:
        return ", ".join("?" for _ in range(count))

    def paging_clause(self, base_query: str, start: int, end: int) -> str:
        # MSSQL ``OFFSET ... ROWS FETCH NEXT ... ROWS ONLY`` requires
        # ``base_query`` to carry an ``ORDER BY`` clause; callers are
        # responsible for supplying one (no portable default exists
        # without column metadata).
        return (
            f"{base_query} OFFSET {start} ROWS "
            f"FETCH NEXT {end - start} ROWS ONLY"
        )


class AsyncOracleDialect(AsyncSqlDialect):
    def quote_identifier(self, name: str) -> str:
        return f'"{name}"'

    def insert_placeholders(self, count: int) -> str:
        return ", ".join(f":{i + 1}" for i in range(count))

    def paging_clause(self, base_query: str, start: int, end: int) -> str:
        # Oracle 12c+ supports the ANSI ``OFFSET ... FETCH NEXT``
        # form. Same caveat as MSSQL: ``base_query`` must carry an
        # ``ORDER BY`` clause for a deterministic page.
        return (
            f"{base_query} OFFSET {start} ROWS "
            f"FETCH NEXT {end - start} ROWS ONLY"
        )


def async_dialect_for(config) -> AsyncSqlDialect:
    """Return the :class:`AsyncSqlDialect` matching ``config.ConnectorType``.

    Mirrors :meth:`AsyncSqlSourceAdapter._connector_for` — both
    dispatchers stay in lock-step: any backend with a wired async
    connector also has a wired async dialect."""
    if config.ConnectorType == ConnectorTypes.POSTGRESQL:
        return AsyncPostgresqlDialect()
    if config.ConnectorType == ConnectorTypes.MYSQL:
        return AsyncMysqlDialect()
    if config.ConnectorType == ConnectorTypes.MSSQL:
        return AsyncMssqlDialect()
    if config.ConnectorType == ConnectorTypes.ORACLE:
        return AsyncOracleDialect()
    raise NotImplementedError(
        f"async dialect for {config.ConnectorType.name} is not "
        f"yet wired in this build (see ADR-0032 follow-ups)"
    )
