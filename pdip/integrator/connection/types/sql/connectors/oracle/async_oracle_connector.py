from ...base import AsyncSqlConnector
from .....domain.types.sql.configuration.base import SqlConnectionConfiguration


class AsyncOracleConnector(AsyncSqlConnector):
    """oracledb async-API connector (ADR-0032 §3 follow-up (a-2)).

    Mirrors :class:`AsyncPostgresqlConnector` — ``oracledb`` is
    imported lazily inside :meth:`connect`. The same package
    powers the sync Oracle path (ADR-0021), but the async API
    surface is exposed via ``oracledb.connect_async``.
    """

    def __init__(self, config: SqlConnectionConfiguration):
        self.config = config
        self.connection = None

    async def connect(self):
        import oracledb
        self.connection = await oracledb.connect_async(
            user=self.config.BasicAuthentication.User,
            password=self.config.BasicAuthentication.Password,
            host=self.config.Server.Host,
            port=int(self.config.Server.Port)
            if self.config.Server.Port is not None
            else None,
            service_name=self.config.Database,
        )

    async def disconnect(self):
        if self.connection is not None:
            await self.connection.close()
            self.connection = None

    async def fetch_count(self, schema, table):
        # Oracle identifiers default to UPPER unless quoted; we
        # quote both halves for case-sensitive parity with the
        # sync sibling.
        query = f'SELECT COUNT(*) FROM "{schema}"."{table}"'
        with self.connection.cursor() as cursor:
            await cursor.execute(query)
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def execute(self, query):
        with self.connection.cursor() as cursor:
            await cursor.execute(query)
            await self.connection.commit()
