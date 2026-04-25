from abc import abstractmethod


class AsyncSqlConnector(object):
    """Async sibling of :class:`SqlConnector` (ADR-0032 §3).

    Concrete implementations live under
    ``pdip/integrator/connection/types/sql/connectors/<flavour>/`` and
    require the ``pdip[async]`` extra. The matching async client
    library (asyncpg, aiomysql, aioodbc, ...) is imported lazily
    inside the method body so importing this module never depends on
    the extra being installed.
    """

    @abstractmethod
    async def connect(self):
        pass

    @abstractmethod
    async def disconnect(self):
        pass

    @abstractmethod
    async def fetch_count(self, schema, table):
        """Return the row count of ``schema.table``. The first
        cross-cutting smoke method — additional read / write
        operations are added per-driver as concrete adapters land."""
        pass

    @abstractmethod
    async def execute(self, query):
        """Run a side-effecting statement (TRUNCATE / DELETE / DDL).
        Concrete connectors are responsible for committing where the
        underlying driver requires an explicit commit (aiomysql /
        aioodbc / oracledb), and for wrapping in an asyncpg
        transaction where appropriate. Used by
        :meth:`AsyncSqlTargetAdapter.clear_data`."""
        pass

    @abstractmethod
    async def fetch_all(self, query):
        """Execute ``query`` and return every row as a list of
        ``dict``-like rows. Used by
        :meth:`AsyncSqlSourceAdapter.get_iterator` and
        :meth:`AsyncSqlSourceAdapter.get_source_data_with_paging`."""
        pass

    @abstractmethod
    async def executemany(self, query, rows):
        """Execute ``query`` once per row in ``rows`` (a sequence of
        positional argument tuples). Used by
        :meth:`AsyncSqlTargetAdapter.write_data` for bulk inserts.
        Concrete connectors must commit if the driver requires it."""
        pass
