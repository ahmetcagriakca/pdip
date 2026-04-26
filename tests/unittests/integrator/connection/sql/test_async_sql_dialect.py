"""Unit tests for ``pdip.integrator.connection.types.sql.base.async_sql_dialect``
(ADR-0032 §3 follow-up (a-3)).

Pin the per-backend SQL fragments produced by each
:class:`AsyncSqlDialect` subclass — placeholder ladder, identifier
quoting, paging clause, and TRUNCATE — plus the dispatcher's
mapping from ``ConnectorTypes`` to the matching dialect.

These fragments are what the async adapter layer
(:class:`AsyncSqlSourceAdapter` / :class:`AsyncSqlTargetAdapter`)
splices into ``executemany`` / ``fetch_all`` queries when driving
the async connectors. Pinning them here gives a fast,
DB-independent regression net for the dialect-specific call sites
that the backend integration tests verify end-to-end.
"""

from unittest import TestCase
from unittest.mock import MagicMock

from pdip.integrator.connection.domain.enums import ConnectorTypes
from pdip.integrator.connection.types.sql.base.async_sql_dialect import (
    AsyncMssqlDialect,
    AsyncMysqlDialect,
    AsyncOracleDialect,
    AsyncPostgresqlDialect,
    async_dialect_for,
)


# ---------------------------------------------------------------------------
# Postgres dialect — asyncpg ``$N`` placeholders + double-quoted identifiers.
# ---------------------------------------------------------------------------


class AsyncPostgresqlDialectShape(TestCase):
    def test_quote_identifier_uses_double_quotes(self):
        self.assertEqual(
            AsyncPostgresqlDialect().quote_identifier("name"), '"name"'
        )

    def test_quote_table_joins_schema_and_table_with_dot(self):
        self.assertEqual(
            AsyncPostgresqlDialect().quote_table("public", "users"),
            '"public"."users"',
        )

    def test_insert_placeholders_renders_dollar_ladder_one_based(self):
        # asyncpg requires positional ``$N`` placeholders that are
        # 1-based; rendering them 0-based silently breaks the bind.
        self.assertEqual(
            AsyncPostgresqlDialect().insert_placeholders(3), "$1, $2, $3"
        )

    def test_insert_placeholders_zero_count_is_empty_string(self):
        self.assertEqual(AsyncPostgresqlDialect().insert_placeholders(0), "")

    def test_paging_clause_uses_limit_offset(self):
        self.assertEqual(
            AsyncPostgresqlDialect().paging_clause(
                "SELECT * FROM t", 5, 15
            ),
            "SELECT * FROM t LIMIT 10 OFFSET 5",
        )

    def test_truncate_query_double_quoted(self):
        self.assertEqual(
            AsyncPostgresqlDialect().truncate_query("public", "users"),
            'TRUNCATE TABLE "public"."users"',
        )


# ---------------------------------------------------------------------------
# MySQL dialect — aiomysql ``%s`` placeholders + backtick identifiers.
# ---------------------------------------------------------------------------


class AsyncMysqlDialectShape(TestCase):
    def test_quote_identifier_uses_backticks(self):
        self.assertEqual(AsyncMysqlDialect().quote_identifier("col"), "`col`")

    def test_quote_table_joins_schema_and_table_with_dot(self):
        self.assertEqual(
            AsyncMysqlDialect().quote_table("test_pdi", "users"),
            "`test_pdi`.`users`",
        )

    def test_insert_placeholders_renders_percent_s_only(self):
        # aiomysql expects ``%s`` for every positional binding,
        # regardless of column count.
        self.assertEqual(
            AsyncMysqlDialect().insert_placeholders(3), "%s, %s, %s"
        )

    def test_paging_clause_uses_limit_offset(self):
        self.assertEqual(
            AsyncMysqlDialect().paging_clause("SELECT * FROM t", 0, 10),
            "SELECT * FROM t LIMIT 10 OFFSET 0",
        )

    def test_truncate_query_backtick_quoted(self):
        self.assertEqual(
            AsyncMysqlDialect().truncate_query("test_pdi", "u"),
            "TRUNCATE TABLE `test_pdi`.`u`",
        )


# ---------------------------------------------------------------------------
# MSSQL dialect — aioodbc ``?`` placeholders + bracket identifiers +
# ANSI ``OFFSET ... FETCH NEXT`` paging.
# ---------------------------------------------------------------------------


class AsyncMssqlDialectShape(TestCase):
    def test_quote_identifier_uses_square_brackets(self):
        self.assertEqual(AsyncMssqlDialect().quote_identifier("c"), "[c]")

    def test_quote_table_joins_schema_and_table_with_dot(self):
        self.assertEqual(
            AsyncMssqlDialect().quote_table("dbo", "u"), "[dbo].[u]"
        )

    def test_insert_placeholders_renders_question_marks(self):
        self.assertEqual(AsyncMssqlDialect().insert_placeholders(2), "?, ?")

    def test_paging_clause_uses_offset_rows_fetch_next(self):
        # MSSQL requires the source query to carry an ``ORDER BY``
        # for ``OFFSET`` to be deterministic — the dialect helper
        # itself does not inject one.
        self.assertEqual(
            AsyncMssqlDialect().paging_clause(
                "SELECT * FROM t ORDER BY id", 5, 15
            ),
            "SELECT * FROM t ORDER BY id "
            "OFFSET 5 ROWS FETCH NEXT 10 ROWS ONLY",
        )

    def test_truncate_query_bracket_quoted(self):
        self.assertEqual(
            AsyncMssqlDialect().truncate_query("dbo", "u"),
            "TRUNCATE TABLE [dbo].[u]",
        )


# ---------------------------------------------------------------------------
# Oracle dialect — oracledb ``:N`` placeholders + double-quoted identifiers
# + ANSI ``OFFSET ... FETCH NEXT`` paging.
# ---------------------------------------------------------------------------


class AsyncOracleDialectShape(TestCase):
    def test_quote_identifier_uses_double_quotes(self):
        self.assertEqual(AsyncOracleDialect().quote_identifier("c"), '"c"')

    def test_quote_table_joins_schema_and_table_with_dot(self):
        self.assertEqual(
            AsyncOracleDialect().quote_table("PDI", "T"), '"PDI"."T"'
        )

    def test_insert_placeholders_renders_colon_ladder_one_based(self):
        # oracledb async accepts both ``:1, :2`` (positional) and
        # ``:name`` (named) bindings; we stick with the positional
        # form so the same row-tuple shape works for every backend.
        self.assertEqual(
            AsyncOracleDialect().insert_placeholders(3), ":1, :2, :3"
        )

    def test_paging_clause_uses_offset_rows_fetch_next(self):
        self.assertEqual(
            AsyncOracleDialect().paging_clause(
                'SELECT * FROM "T" ORDER BY ID', 0, 10
            ),
            'SELECT * FROM "T" ORDER BY ID '
            "OFFSET 0 ROWS FETCH NEXT 10 ROWS ONLY",
        )

    def test_truncate_query_double_quoted(self):
        self.assertEqual(
            AsyncOracleDialect().truncate_query("PDI", "T"),
            'TRUNCATE TABLE "PDI"."T"',
        )


# ---------------------------------------------------------------------------
# Dispatcher — ``async_dialect_for`` maps ``ConnectorTypes`` to dialect
# classes in lock-step with ``_connector_for`` on the adapters.
# ---------------------------------------------------------------------------


class AsyncDialectForRoutesByConnectorType(TestCase):
    @staticmethod
    def _config(connector_type):
        config = MagicMock()
        config.ConnectorType = connector_type
        return config

    def test_postgresql_returns_async_postgresql_dialect(self):
        result = async_dialect_for(self._config(ConnectorTypes.POSTGRESQL))

        self.assertIsInstance(result, AsyncPostgresqlDialect)

    def test_mysql_returns_async_mysql_dialect(self):
        result = async_dialect_for(self._config(ConnectorTypes.MYSQL))

        self.assertIsInstance(result, AsyncMysqlDialect)

    def test_mssql_returns_async_mssql_dialect(self):
        result = async_dialect_for(self._config(ConnectorTypes.MSSQL))

        self.assertIsInstance(result, AsyncMssqlDialect)

    def test_oracle_returns_async_oracle_dialect(self):
        result = async_dialect_for(self._config(ConnectorTypes.ORACLE))

        self.assertIsInstance(result, AsyncOracleDialect)

    def test_unsupported_connector_raises_not_implemented(self):
        # ``ConnectorTypes.CLICKHOUSE`` is wired in the sync path but
        # the async dialect set is gated to the four documented
        # async-extra backends; this is the explicit
        # ``NotImplementedError`` per ADR-0032 §3 (a) until a
        # CLICKHOUSE async client lands.
        config = self._config(ConnectorTypes.CLICKHOUSE)

        with self.assertRaises(NotImplementedError) as ctx:
            async_dialect_for(config)

        self.assertIn("async dialect", str(ctx.exception))
        self.assertIn("CLICKHOUSE", str(ctx.exception))
