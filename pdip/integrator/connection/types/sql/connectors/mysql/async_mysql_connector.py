from ...base import AsyncSqlConnector
from .....domain.types.sql.configuration.base import SqlConnectionConfiguration


class AsyncMysqlConnector(AsyncSqlConnector):
    """aiomysql-backed MySQL connector (ADR-0032 §3 follow-up (a-2)).

    Mirrors :class:`AsyncPostgresqlConnector` — ``aiomysql`` is
    imported lazily inside :meth:`connect` so the class can be
    constructed even when ``pdip[async]`` is not installed.
    """

    def __init__(self, config: SqlConnectionConfiguration):
        self.config = config
        self.connection = None

    async def connect(self):
        import aiomysql
        self.connection = await aiomysql.connect(
            host=self.config.Server.Host,
            port=int(self.config.Server.Port)
            if self.config.Server.Port is not None
            else None,
            user=self.config.BasicAuthentication.User,
            password=self.config.BasicAuthentication.Password,
            db=self.config.Database,
        )

    async def disconnect(self):
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    async def fetch_count(self, schema, table):
        # MySQL identifiers use backtick quoting; no schema for
        # default db, but we still emit the schema-qualified form
        # for consistency with the sync sibling's contract.
        query = f"SELECT COUNT(*) FROM `{schema}`.`{table}`"
        async with self.connection.cursor() as cursor:
            await cursor.execute(query)
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def execute(self, query):
        async with self.connection.cursor() as cursor:
            await cursor.execute(query)
            await self.connection.commit()
