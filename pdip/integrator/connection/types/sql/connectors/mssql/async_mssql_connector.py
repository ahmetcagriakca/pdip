from ...base import AsyncSqlConnector
from .....domain.types.sql.configuration.base import SqlConnectionConfiguration


class AsyncMssqlConnector(AsyncSqlConnector):
    """aioodbc-backed MSSQL connector (ADR-0032 §3 follow-up (a-2)).

    Mirrors :class:`AsyncPostgresqlConnector` — ``aioodbc`` is
    imported lazily inside :meth:`connect` so the class can be
    constructed even when ``pdip[async]`` is not installed. Uses
    the same ODBC Driver 18 configuration the sync MSSQL connector
    relies on at the host level.
    """

    def __init__(self, config: SqlConnectionConfiguration):
        self.config = config
        self.connection = None

    async def connect(self):
        import aioodbc
        dsn = (
            f"Driver={{ODBC Driver 18 for SQL Server}};"
            f"Server={self.config.Server.Host},{self.config.Server.Port};"
            f"Database={self.config.Database};"
            f"UID={self.config.BasicAuthentication.User};"
            f"PWD={self.config.BasicAuthentication.Password};"
            "TrustServerCertificate=yes;"
        )
        self.connection = await aioodbc.connect(dsn=dsn)

    async def disconnect(self):
        if self.connection is not None:
            await self.connection.close()
            self.connection = None

    async def fetch_count(self, schema, table):
        # MSSQL identifiers use square-bracket quoting.
        query = f"SELECT COUNT(*) FROM [{schema}].[{table}]"
        async with self.connection.cursor() as cursor:
            await cursor.execute(query)
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def execute(self, query):
        async with self.connection.cursor() as cursor:
            await cursor.execute(query)
            await self.connection.commit()

    async def fetch_all(self, query):
        # aioodbc returns row tuples + column descriptions; we coerce
        # to plain dicts so the strategy layer sees the same shape it
        # gets from asyncpg / aiomysql.
        async with self.connection.cursor() as cursor:
            await cursor.execute(query)
            columns = [d[0] for d in cursor.description]
            rows = await cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]

    async def executemany(self, query, rows):
        async with self.connection.cursor() as cursor:
            await cursor.executemany(query, rows)
            await self.connection.commit()
