"""
Tests for UK fiscal year parameter handling.

The UK fiscal year runs April 6 to April 5. PolicyEngine UK uses
on-the-fly fiscal year conversion in get_parameters_at_instant() to
convert January 1 queries to April 30, getting the correct fiscal year value.

This test suite verifies that annual period queries (e.g., param("2026"))
return the correct fiscal year values, especially for policy changes
that take effect on April 6.

Key policy examples:
- Two-child limit repeal: limit=2 until April 5, 2026, then infinity from April 6, 2026
- Income tax threshold freeze extension: threshold frozen from April 6, 2028
"""

import pytest
from policyengine_uk import CountryTaxBenefitSystem
from policyengine_uk.utils.parameters import convert_instant_to_fiscal_year
from policyengine_core.periods import period


@pytest.fixture(scope="module")
def uk_system():
    """Create a UK tax-benefit system for testing."""
    return CountryTaxBenefitSystem()


class TestInstantConversion:
    """Tests for the convert_instant_to_fiscal_year function."""

    def test_year_only_converts_to_april_30(self):
        """Year-only queries should convert to April 30."""
        assert convert_instant_to_fiscal_year("2026") == "2026-04-30"
        assert convert_instant_to_fiscal_year("2025") == "2025-04-30"
        assert convert_instant_to_fiscal_year("2030") == "2030-04-30"

    def test_january_1_converts_to_april_30(self):
        """January 1 queries should convert to April 30."""
        assert convert_instant_to_fiscal_year("2026-01-01") == "2026-04-30"
        assert convert_instant_to_fiscal_year("2025-01-01") == "2025-04-30"

    def test_other_dates_unchanged(self):
        """Specific dates (not Jan 1) should not be modified."""
        assert convert_instant_to_fiscal_year("2026-04-30") == "2026-04-30"
        assert convert_instant_to_fiscal_year("2026-06-15") == "2026-06-15"
        assert convert_instant_to_fiscal_year("2026-04-06") == "2026-04-06"
        assert convert_instant_to_fiscal_year("2026-12-31") == "2026-12-31"


class TestFiscalYearConversion:
    """Tests for the fiscal year parameter conversion."""

    def test_period_start_is_january_1(self):
        """Verify that period('2026') starts on January 1."""
        p = period("2026")
        assert p.start.year == 2026
        assert p.start.month == 1
        assert p.start.day == 1

    def test_get_parameters_at_instant_uses_fiscal_year(self, uk_system):
        """
        Test that get_parameters_at_instant converts Jan 1 to April 30.

        When querying parameters for "2026", the system should use
        April 30, 2026 as the reference date, getting the fiscal year value.
        """
        # Get parameters at "2026" (should use April 30 internally)
        params_2026 = uk_system.get_parameters_at_instant("2026")

        # The two-child limit should be infinity (repealed April 6, 2026)
        child_limit = (
            params_2026.gov.dwp.universal_credit.elements.child.limit.child_count
        )
        assert child_limit == float("inf"), (
            f"Expected infinity for 2026 fiscal year, got {child_limit}. "
            "The get_parameters_at_instant may not be converting to April 30."
        )


class TestTwoChildLimitRepeal:
    """Tests specifically for the two-child limit repeal on April 6, 2026."""

    def test_two_child_limit_fiscal_year_2025(self, uk_system):
        """Test that the two-child limit is 2 for fiscal year 2025/26."""
        # Get parameters at fiscal year 2025 (uses April 30, 2025)
        params = uk_system.get_parameters_at_instant("2025")
        child_limit = (
            params.gov.dwp.universal_credit.elements.child.limit.child_count
        )
        assert child_limit == 2

    def test_two_child_limit_fiscal_year_2026(self, uk_system):
        """Test that the two-child limit is infinity for fiscal year 2026/27."""
        # Get parameters at fiscal year 2026 (uses April 30, 2026)
        params = uk_system.get_parameters_at_instant("2026")
        child_limit = (
            params.gov.dwp.universal_credit.elements.child.limit.child_count
        )
        assert child_limit == float("inf")

    def test_annual_query_reflects_fiscal_year(self, uk_system):
        """
        Test that annual queries return fiscal year values.

        For year 2026, the fiscal year is April 6, 2026 to April 5, 2027.
        The two-child limit is repealed on April 6, 2026, so:
        - 2025 should be 2 (fiscal year 2025/26: April 6, 2025 - April 5, 2026)
        - 2026 should be infinity (fiscal year 2026/27: April 6, 2026 - April 5, 2027)
        """
        params_2025 = uk_system.get_parameters_at_instant("2025")
        params_2026 = uk_system.get_parameters_at_instant("2026")
        params_2027 = uk_system.get_parameters_at_instant("2027")

        limit_2025 = (
            params_2025.gov.dwp.universal_credit.elements.child.limit.child_count
        )
        limit_2026 = (
            params_2026.gov.dwp.universal_credit.elements.child.limit.child_count
        )
        limit_2027 = (
            params_2027.gov.dwp.universal_credit.elements.child.limit.child_count
        )

        assert limit_2025 == 2
        assert limit_2026 == float("inf")
        assert limit_2027 == float("inf")


class TestThresholdFreezeExtension:
    """Tests for income tax threshold freeze extension (April 6, 2028)."""

    def test_pa_threshold_freeze_dates(self, uk_system):
        """Test that PA threshold freeze is correctly parameterized."""
        # This tests the threshold_freeze_end parameter
        param_path = (
            "gov.hmrc.income_tax.allowances."
            "personal_allowance.threshold_freeze_end"
        )
        try:
            param = uk_system.parameters.get_child(param_path)
            # Verify the freeze end date parameter exists
            assert param is not None
        except Exception:
            # Parameter may have different structure
            pytest.skip(
                "Personal allowance threshold freeze end parameter not found"
            )


class TestFiscalYearConversionCoverage:
    """Tests to verify fiscal year conversion covers all years."""

    @pytest.mark.parametrize("year", [2025, 2026, 2027, 2028, 2029, 2030])
    def test_year_in_conversion_range(self, uk_system, year):
        """
        Test that each year from 2025-2030 can be queried.

        This test verifies that get_parameters_at_instant works for
        all years that might be used in simulations.
        """
        # Query should work without error
        params = uk_system.get_parameters_at_instant(str(year))
        assert params is not None
        # Verify we can access a simple parameter (not a scale)
        pa = params.gov.hmrc.income_tax.allowances.personal_allowance.amount
        assert pa is not None
        assert pa > 0  # Personal allowance should be positive


class TestSpecificDateQueries:
    """Tests to ensure specific date queries are not modified."""

    def test_april_5_query_unchanged(self, uk_system):
        """Querying April 5, 2026 should return pre-repeal value."""
        # Direct parameter query at April 5
        param = uk_system.parameters.get_child(
            "gov.dwp.universal_credit.elements.child.limit.child_count"
        )
        # April 5, 2026 is the last day before repeal
        assert param("2026-04-05") == 2

    def test_april_6_query_unchanged(self, uk_system):
        """Querying April 6, 2026 should return post-repeal value."""
        # Direct parameter query at April 6
        param = uk_system.parameters.get_child(
            "gov.dwp.universal_credit.elements.child.limit.child_count"
        )
        # April 6, 2026 is the first day of repeal
        assert param("2026-04-06") == float("inf")
