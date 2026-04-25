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
