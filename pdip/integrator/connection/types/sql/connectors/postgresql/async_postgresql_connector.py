from ...base import AsyncSqlConnector
from .....domain.types.sql.configuration.base import SqlConnectionConfiguration


class AsyncPostgresqlConnector(AsyncSqlConnector):
    """asyncpg-backed Postgres connector (ADR-0032 §3).

    ``asyncpg`` is imported lazily inside :meth:`connect` so the
    class can be constructed even when ``pdip[async]`` is not
    installed — the failure surfaces only when the user actually
    asks for an async connection. Every other method assumes
    :meth:`connect` has succeeded.
    """

    def __init__(self, config: SqlConnectionConfiguration):
        self.config = config
        self.connection = None

    async def connect(self):
        import asyncpg
        self.connection = await asyncpg.connect(
            host=self.config.Server.Host,
            port=int(self.config.Server.Port)
            if self.config.Server.Port is not None
            else None,
            user=self.config.BasicAuthentication.User,
            password=self.config.BasicAuthentication.Password,
            database=self.config.Database,
        )

    async def disconnect(self):
        if self.connection is not None:
            await self.connection.close()
            self.connection = None

    async def fetch_count(self, schema, table):
        # Postgres identifiers are case-sensitive when quoted; the
        # sync sibling already pairs schemas + tables this way.
        query = f'SELECT COUNT(*) FROM "{schema}"."{table}"'
        return await self.connection.fetchval(query)
