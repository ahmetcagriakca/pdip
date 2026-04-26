from ...base import AsyncSqlConnector
from .....domain.types.sql.configuration.base import SqlConnectionConfiguration


class AsyncMssqlConnector(AsyncSqlConnector):
    """aioodbc-backed MSSQL connector (ADR-0032 §3 follow-up (a-2)).

    Mirrors :class:`AsyncPostgresqlConnector` — ``aioodbc`` is
    imported lazily inside :meth:`connect` so the class can be
    constructed even when ``pdip[async]`` is not installed. The
    ODBC driver name is **discovered** via ``pyodbc.drivers()``
    (mirroring ``MssqlConnector.find_driver_name``) so the
    connector works against whichever ``ODBC Driver NN for SQL
    Server`` is installed on the host — the integration-tests CI
    runner uses Driver 17, the local docker-compose fixture
    typically has Driver 18; both must work without code changes.
    """

    def __init__(self, config: SqlConnectionConfiguration):
        self.config = config
        self.connection = None

    async def connect(self):
        import aioodbc
        driver_name = self._driver_name()
        dsn = (
            f"Driver={{{driver_name}}};"
            f"Server={self.config.Server.Host},{self.config.Server.Port};"
            f"Database={self.config.Database};"
            f"UID={self.config.BasicAuthentication.User};"
            f"PWD={self.config.BasicAuthentication.Password};"
            "TrustServerCertificate=yes;"
        )
        self.connection = await aioodbc.connect(dsn=dsn)

    @staticmethod
    def _driver_name():
        # Mirrors ``MssqlConnector.find_driver_name`` — pick the
        # newest ``... for SQL Server`` driver pyodbc reports, fall
        # back to anything mentioning ``SQL Server`` / ``FreeTDS``,
        # then to the first installed driver. Lazy-imports
        # ``pyodbc`` (a transitive dep of ``aioodbc`` so it is
        # always available when the async-extra is installed).
        import pyodbc
        drivers = pyodbc.drivers()
        for_sql_server = [d for d in drivers if "for SQL Server" in d]
        if for_sql_server:
            return list(reversed(for_sql_server))[0]
        sql_server_or_freetds = [
            d for d in drivers if "SQL Server" in d or "FreeTDS" in d
        ]
        if sql_server_or_freetds:
            return list(reversed(sql_server_or_freetds))[0]
        return drivers[0]

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
