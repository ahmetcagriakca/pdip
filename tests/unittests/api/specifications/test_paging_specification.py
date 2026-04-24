"""Unit tests for ``pdip.api.specifications.paging_specification.PagingSpecification``.

The specification normalises paging parameters (PageSize / PageNumber)
into a ``(page_size, offset)`` tuple with defaults and bounds applied.
These tests pin down the default fallbacks, the min / max clamp, and
the offset arithmetic.
"""

from unittest import TestCase

from pdip.api.request_parameter import PagingParameter
from pdip.api.specifications.paging_specification import PagingSpecification


class PagingSpecificationNormalisesParameters(TestCase):
    def setUp(self):
        self.spec = PagingSpecification()

    def test_defaults_applied_when_both_fields_none(self):
        param = PagingParameter()

        page_size, offset = self.spec.specify(param)

        self.assertEqual(page_size, 10)
        self.assertEqual(offset, 0)

    def test_valid_page_size_and_page_number_computes_offset(self):
        param = PagingParameter(PageNumber=3, PageSize=20)

        page_size, offset = self.spec.specify(param)

        self.assertEqual(page_size, 20)
        self.assertEqual(offset, 40)

    def test_page_size_below_minimum_falls_back_to_default(self):
        param = PagingParameter(PageNumber=2, PageSize=1)

        page_size, offset = self.spec.specify(param)

        self.assertEqual(page_size, 10)
        self.assertEqual(offset, 10)

    def test_page_size_above_maximum_falls_back_to_default(self):
        param = PagingParameter(PageNumber=1, PageSize=500)

        page_size, offset = self.spec.specify(param)

        self.assertEqual(page_size, 10)
        self.assertEqual(offset, 0)

    def test_page_number_below_one_clamped_to_default(self):
        param = PagingParameter(PageNumber=0, PageSize=20)

        page_size, offset = self.spec.specify(param)

        self.assertEqual(page_size, 20)
        self.assertEqual(offset, 0)

    def test_none_page_number_with_valid_size_uses_default_page(self):
        param = PagingParameter(PageNumber=None, PageSize=25)

        page_size, offset = self.spec.specify(param)

        self.assertEqual(page_size, 25)
        self.assertEqual(offset, 0)

    def test_parameter_missing_page_size_attribute_returns_none_pair(self):
        # Arrange — an object with PageNumber but no PageSize attribute
        # at all. ``PagingParameter`` always defines both, so build a
        # bare object to hit the early-return guard.
        class _OnlyPageNumber:
            PageNumber = 1

        # Act
        page_size, offset = self.spec.specify(_OnlyPageNumber())

        # Assert
        self.assertIsNone(page_size)
        self.assertIsNone(offset)
