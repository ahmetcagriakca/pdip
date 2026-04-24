"""Unit tests for
``pdip.api.specifications.order_by_specification.OrderBySpecification``.

The specification turns an ``OrderByParameter`` (a ``"Column"`` or
``"Class.Attr"`` string plus ``Order``) into a SQLAlchemy expression.
``ModuleFinder`` is mocked because these tests pin behaviour, not
filesystem module discovery.
"""

from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import MagicMock

from sqlalchemy import Column, Integer
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql.elements import TextClause, UnaryExpression

from pdip.api.request_parameter import OrderByParameter
from pdip.api.specifications.order_by_specification import OrderBySpecification


_Base = declarative_base()


class _Widget(_Base):
    __tablename__ = "widget_order_spec"
    Id = Column(Integer, primary_key=True)
    Name = Column(Integer)


def _build_spec_with_stub_module(class_name="_Widget"):
    """Return a spec whose ``module_finder.get_module`` yields a module
    containing ``_Widget``."""
    fake_module = SimpleNamespace(_Widget=_Widget)
    module_finder = MagicMock()
    module_finder.get_module.return_value = fake_module
    return OrderBySpecification(module_finder=module_finder), module_finder


class OrderBySpecificationTranslatesParameters(TestCase):
    def test_returns_text_clause_for_single_segment_order_by(self):
        spec, _ = _build_spec_with_stub_module()
        param = OrderByParameter(OrderBy="Name", Order="asc")

        result = spec.specify(param)

        self.assertIsInstance(result, TextClause)
        self.assertEqual(str(result), '"Name" asc')

    def test_returns_column_attribute_for_dotted_order_by_with_asc(self):
        spec, module_finder = _build_spec_with_stub_module()
        param = OrderByParameter(OrderBy="_Widget.Name", Order="asc")

        result = spec.specify(param)

        module_finder.get_module.assert_called_once_with("_Widget")
        self.assertIs(result, _Widget.Name)

    def test_returns_desc_expression_when_order_is_desc(self):
        spec, _ = _build_spec_with_stub_module()
        param = OrderByParameter(OrderBy="_Widget.Name", Order="desc")

        result = spec.specify(param)

        self.assertIsInstance(result, UnaryExpression)
        # The UnaryExpression wraps the column with the desc modifier
        # and renders with a trailing "DESC".
        self.assertIn("DESC", str(result).upper())

    def test_default_order_applied_when_order_is_empty_string(self):
        spec, _ = _build_spec_with_stub_module()
        param = OrderByParameter(OrderBy="_Widget.Name", Order="")

        result = spec.specify(param)

        # Empty order should not produce a desc wrapper; asc returns
        # the attribute itself.
        self.assertIs(result, _Widget.Name)

    def test_returns_none_when_order_by_has_more_than_two_segments(self):
        spec, _ = _build_spec_with_stub_module()
        param = OrderByParameter(OrderBy="a.b.c", Order="asc")

        result = spec.specify(param)

        self.assertIsNone(result)

    def test_returns_none_when_order_by_is_none(self):
        spec, module_finder = _build_spec_with_stub_module()
        param = OrderByParameter(OrderBy=None, Order="asc")

        result = spec.specify(param)

        self.assertIsNone(result)
        module_finder.get_module.assert_not_called()
