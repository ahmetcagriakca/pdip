"""Behavioural tests for ``pdip.html.html_template_service``.

These tests exercise the public surface of ``HtmlTemplateService`` and
``Pagination`` without booting ``Pdi()`` and without any network or
filesystem access, per ADR-0026.
"""

from unittest import TestCase
from unittest.mock import MagicMock

from pdip.configuration.models.application import ApplicationConfig
from pdip.html.html_template_service import HtmlTemplateService, Pagination
from pdip.json import JsonConvert


def _build_service():
    """Factory for a service bound to a throwaway ApplicationConfig."""
    config = ApplicationConfig(root_directory="/tmp/fake", name="test")
    return HtmlTemplateService(application_config=config), config


def _cell(value, style="", cls=""):
    return {"value": value, "style": style, "class": cls}


def _snapshot_mappings():
    return dict(JsonConvert.mappings)


def _restore_mappings(snapshot):
    JsonConvert.mappings.clear()
    JsonConvert.mappings.update(snapshot)


class PaginationStoresConstructorArguments(TestCase):
    def test_pagination_exposes_each_field_passed_to_the_constructor(self):
        # Arrange
        page_url = "/items/{0}"

        # Act
        pagination = Pagination(
            Filter="active",
            Page=2,
            PageUrl=page_url,
            Limit=10,
            TotalPage=5,
            TotalCount=47,
        )

        # Assert
        self.assertEqual(pagination.Filter, "active")
        self.assertEqual(pagination.Page, 2)
        self.assertEqual(pagination.PageUrl, page_url)
        self.assertEqual(pagination.Limit, 10)
        self.assertEqual(pagination.TotalPage, 5)
        self.assertEqual(pagination.TotalCount, 47)

    def test_pagination_defaults_every_field_to_none(self):
        # Arrange / Act
        pagination = Pagination()

        # Assert
        self.assertIsNone(pagination.Filter)
        self.assertIsNone(pagination.Page)
        self.assertIsNone(pagination.PageUrl)
        self.assertIsNone(pagination.Limit)
        self.assertIsNone(pagination.TotalPage)
        self.assertIsNone(pagination.TotalCount)


class HtmlTemplateServiceHoldsInjectedConfig(TestCase):
    def test_service_stores_the_application_config_passed_in(self):
        # Arrange
        config = ApplicationConfig(root_directory="/srv/app", name="pdip")

        # Act
        service = HtmlTemplateService(application_config=config)

        # Assert
        self.assertIs(service.application_config, config)
        self.assertEqual(service.application_config.root_directory, "/srv/app")


class DefaultCssExposesWrapperAndPaginationBlocks(TestCase):
    def test_default_css_includes_wrapper_pagination_and_breadcrumb_rules(self):
        # Arrange
        service, _ = _build_service()

        # Act
        css = service.default_css

        # Assert
        self.assertIn(".wrapper", css)
        self.assertIn(".pagination", css)
        self.assertIn(".pagination a.active", css)
        self.assertIn("ul.breadcrumb", css)
        self.assertIn(".pdi-column", css)
        self.assertIn(".pdi-row", css)


class MailHtmlTemplateWrapsBodyInHtmlDocument(TestCase):
    def test_template_embeds_body_and_default_css_when_no_css_supplied(self):
        # Arrange
        service, _ = _build_service()
        body = "<p>hello world</p>"

        # Act
        html = service.mail_html_template(body)

        # Assert
        self.assertIn("<!DOCTYPE html", html)
        self.assertIn("<p>hello world</p>", html)
        self.assertIn(".wrapper", html)  # default CSS leaked in

    def test_template_uses_override_css_when_caller_supplies_one(self):
        # Arrange
        service, _ = _build_service()
        body = "<p>msg</p>"
        override = ".custom-class { color: red; }"

        # Act
        html = service.mail_html_template(body, mail_css=override)

        # Assert
        self.assertIn(override, html)
        self.assertNotIn(".wrapper", html)  # default CSS suppressed
        self.assertIn("<p>msg</p>", html)


class RenderHtmlWrapsContentInWrapperDiv(TestCase):
    def test_render_html_embeds_content_in_wrapper_and_full_document(self):
        # Arrange
        service, _ = _build_service()

        # Act
        result = service.render_html("<span>inner</span>")

        # Assert
        self.assertIn('<div class="wrapper">', result)
        self.assertIn("<span>inner</span>", result)
        self.assertIn("<!DOCTYPE html", result)


class GetNullableDictValueReturnsNoneForMissingKey(TestCase):
    def test_present_key_returns_value_and_missing_key_returns_none(self):
        # Arrange
        service, _ = _build_service()
        source = {"a": 1, "b": None}

        # Act
        present = service.get_nullable_dict_value(source, "a")
        missing = service.get_nullable_dict_value(source, "missing")
        none_value = service.get_nullable_dict_value(source, "b")

        # Assert
        self.assertEqual(present, 1)
        self.assertIsNone(missing)
        # The method returns the stored value even when it is None
        # because it only checks key membership.
        self.assertIsNone(none_value)


class GetDictValueReturnsEmptyStringForMissingOrNone(TestCase):
    def test_returns_value_for_present_key(self):
        # Arrange
        service, _ = _build_service()

        # Act
        result = service.get_dict_value({"x": "hello"}, "x")

        # Assert
        self.assertEqual(result, "hello")

    def test_returns_empty_string_when_key_is_absent(self):
        # Arrange
        service, _ = _build_service()

        # Act
        result = service.get_dict_value({"x": "hello"}, "y")

        # Assert
        self.assertEqual(result, "")

    def test_returns_empty_string_when_value_is_none(self):
        # Arrange
        service, _ = _build_service()

        # Act
        result = service.get_dict_value({"x": None}, "x")

        # Assert
        self.assertEqual(result, "")


class PrepareTableDataDynamicBuildsRowsAndPaginationMetadata(TestCase):
    def test_without_pagination_returns_rows_built_from_prepare_row(self):
        # Arrange
        service, _ = _build_service()
        query = MagicMock()
        query.__iter__.return_value = iter([{"v": 1}, {"v": 2}])
        headers = [{"value": "V"}]

        def prepare_row(row):
            return {"data": [{"value": row["v"]}]}

        # Act
        result = service.prepare_table_data_dynamic(
            query, headers, prepare_row
        )

        # Assert
        self.assertEqual(result["columns"], headers)
        self.assertEqual(len(result["rows"]), 2)
        self.assertEqual(result["rows"][0]["data"][0]["value"], 1)
        self.assertIsNone(result["pagination"])

    def test_sortable_applies_order_by_text_to_query(self):
        # Arrange
        service, _ = _build_service()
        query = MagicMock()
        ordered = MagicMock()
        ordered.__iter__.return_value = iter([])
        query.order_by.return_value = ordered

        # Act
        result = service.prepare_table_data_dynamic(
            query, headers=[], prepare_row=lambda r: r, sortable="name asc"
        )

        # Assert
        query.order_by.assert_called_once()
        self.assertEqual(result["rows"], [])
        self.assertIsNone(result["pagination"])

    def test_pagination_defaults_limit_and_page_when_values_are_missing(self):
        # Arrange
        service, _ = _build_service()
        query = MagicMock()
        query.count.return_value = 130
        limited = MagicMock()
        offsetted = MagicMock()
        query.limit.return_value = limited
        limited.offset.return_value = offsetted
        offsetted.__iter__.return_value = iter([])
        pagination = Pagination(PageUrl="/p", Filter=None)

        # Act
        result = service.prepare_table_data_dynamic(
            query, headers=[], prepare_row=lambda r: r, pagination=pagination
        )

        # Assert
        # After the key-alignment fix, the emitted dict uses the same
        # names as ``Pagination.__init__`` (``Page`` + ``TotalCount``)
        # so downstream code (e.g. ``render_table``) can round-trip it.
        self.assertEqual(pagination.Limit, 50)
        self.assertEqual(pagination.Page, 1)
        self.assertEqual(result["pagination"]["TotalCount"], 130)
        self.assertEqual(result["pagination"]["Page"], 1)
        self.assertEqual(result["pagination"]["Limit"], 50)
        self.assertEqual(result["pagination"]["TotalPage"], 3)  # 130/50 + 1
        self.assertNotIn("PageNumber", result["pagination"])
        self.assertNotIn("Count", result["pagination"])
        query.limit.assert_called_once_with(50)
        limited.offset.assert_called_once_with(0)

    def test_pagination_uses_provided_limit_and_page_within_range(self):
        # Arrange
        service, _ = _build_service()
        query = MagicMock()
        query.count.return_value = 100
        limited = MagicMock()
        offsetted = MagicMock()
        query.limit.return_value = limited
        limited.offset.return_value = offsetted
        offsetted.__iter__.return_value = iter([{"a": 1}])
        pagination = Pagination(PageUrl="/p", Limit=20, Page=2, Filter="f")

        # Act
        result = service.prepare_table_data_dynamic(
            query,
            headers=[{"value": "A"}],
            prepare_row=lambda r: {"data": [{"value": r["a"]}]},
            pagination=pagination,
        )

        # Assert
        query.limit.assert_called_once_with(20)
        limited.offset.assert_called_once_with(20)  # (2-1)*20
        self.assertEqual(result["pagination"]["Page"], 2)
        self.assertEqual(result["pagination"]["Filter"], "f")
        self.assertEqual(len(result["rows"]), 1)

    def test_pagination_resets_limit_when_above_200(self):
        # Arrange
        service, _ = _build_service()
        query = MagicMock()
        query.count.return_value = 0
        limited = MagicMock()
        offsetted = MagicMock()
        query.limit.return_value = limited
        limited.offset.return_value = offsetted
        offsetted.__iter__.return_value = iter([])
        pagination = Pagination(PageUrl="/p", Limit=500, Page=1)

        # Act
        service.prepare_table_data_dynamic(
            query, headers=[], prepare_row=lambda r: r, pagination=pagination
        )

        # Assert
        self.assertEqual(pagination.Limit, 50)


class RenderTableEmitsTableHtmlWithHeadersAndRows(TestCase):
    def setUp(self):
        self._mappings_snapshot = _snapshot_mappings()

    def tearDown(self):
        _restore_mappings(self._mappings_snapshot)

    def test_table_html_contains_headers_row_numbers_and_values(self):
        # Arrange
        service, _ = _build_service()
        source = {
            "columns": [_cell("Name"), _cell("Age")],
            "rows": [
                {"data": [_cell("Ada"), _cell("36")]},
                {"data": [_cell("Linus"), _cell("54")]},
            ],
            "pagination": None,
        }

        # Act
        html = service.render_table(source)

        # Assert
        self.assertIn("<table", html)
        self.assertIn(">Name<", html)
        self.assertIn(">Age<", html)
        self.assertIn(">Ada<", html)
        self.assertIn(">Linus<", html)
        # Row numbering starts at 1.
        self.assertIn(">1<", html)
        self.assertIn(">2<", html)
        # Default width is 100%.
        self.assertIn('width="100%"', html)

    def test_explicit_width_overrides_default(self):
        # Arrange
        service, _ = _build_service()
        source = {"columns": [], "rows": [], "pagination": None}

        # Act
        html = service.render_table(source, width="640")

        # Assert
        self.assertIn('width="640"', html)

    def test_pagination_section_is_omitted_when_source_has_no_pagination(self):
        # Arrange
        service, _ = _build_service()
        source = {
            "columns": [_cell("N")],
            "rows": [{"data": [_cell("1")]}],
            "pagination": None,
        }

        # Act
        html = service.render_table(source)

        # Assert
        self.assertNotIn('class="pagination"', html)
        self.assertNotIn('class="active"', html)

    def test_pagination_block_renders_when_keys_match_pagination_init(self):
        # Regression for the key-alignment fix: the pagination dict
        # emitted by ``prepare_table_data_dynamic`` must now round-trip
        # through ``JsonConvert.FromJSON`` into a ``Pagination`` object
        # with a working ``Page`` attribute and drive the active-class
        # highlight on the current page.
        service, _ = _build_service()
        pagination_json = {
            "PageUrl": "/items/{0}",
            "Page": 2,
            "Limit": 10,
            "TotalCount": 25,
            "TotalPage": 3,
            "Filter": "",
        }
        source = {
            "columns": [_cell("N")],
            "rows": [{"data": [_cell("1")]}],
            "pagination": pagination_json,
        }

        html = service.render_table(source)

        # The pagination div is rendered; the active page is the one
        # matching ``Page`` (==2), and there are TotalPage links in all.
        self.assertIn('class="pagination"', html)
        self.assertIn('class="active"', html)
        self.assertEqual(html.count('<a href='), 3)
        # Only page 2 got the active class.
        self.assertIn('class="active">2<', html)
        self.assertNotIn('class="active">1<', html)
        self.assertNotIn('class="active">3<', html)
