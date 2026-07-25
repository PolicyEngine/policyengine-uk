"""
Tests for UK fiscal year parameter handling.

The UK fiscal year runs April 6 to April 5. PolicyEngine UK converts
parameters to use fiscal year values by sampling at April 30 of each year.

This test suite verifies that annual period queries (e.g., param("2026"))
return the correct fiscal year values, especially for policy changes
that take effect on April 6.

Key policy example:
- Two-child limit repeal: limit=2 until April 5, 2026, then infinity
  from April 6, 2026
"""

import pytest
from policyengine_uk import CountryTaxBenefitSystem


@pytest.fixture(scope="module")
def uk_system():
    """Create a UK tax-benefit system for testing."""
    return CountryTaxBenefitSystem()


class TestTwoChildLimitRepeal:
    """Tests for the two-child limit repeal on April 6, 2026."""

    def test_two_child_limit_fiscal_year_2025(self, uk_system):
        """Test that the two-child limit is 2 for fiscal year 2025/26."""
        params = uk_system.get_parameters_at_instant("2025")
        child_limit = params.gov.dwp.universal_credit.elements.child.limit.child_count
        assert child_limit == 2

    def test_two_child_limit_fiscal_year_2026(self, uk_system):
        """Test that the two-child limit is infinity for fiscal year 2026/27.

        This is the key test case - the repeal happens on April 6, 2026.
        When querying for "2026", the system should use April 30, 2026
        as the reference date, which is AFTER the repeal date.
        """
        params = uk_system.get_parameters_at_instant("2026")
        child_limit = params.gov.dwp.universal_credit.elements.child.limit.child_count
        assert child_limit == float("inf"), (
            f"Expected infinity for 2026 fiscal year, got {child_limit}. "
            "The fiscal year conversion may not be covering 2026."
        )

    def test_annual_query_reflects_fiscal_year(self, uk_system):
        """
        Test that annual queries return fiscal year values.

        For year 2026, the fiscal year is April 6, 2026 to April 5, 2027.
        The two-child limit is repealed on April 6, 2026, so:
        - 2025 should be 2 (fiscal year 2025/26)
        - 2026 should be infinity (fiscal year 2026/27)
        - 2027 should be infinity (fiscal year 2027/28)
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


class TestFiscalYearBoundary:
    """Tests for fiscal year boundary behavior.

    Note: After fiscal year conversion, the entire year is set to the
    April 30 value. This means January-March dates return the fiscal
    year value for that calendar year, not the previous fiscal year.
    """

    def test_january_2026_returns_fiscal_year_2026_value(self, uk_system):
        """January 2026 should return fiscal year 2026/27 value.

        After fiscal year conversion, the year 2026 is set to the
        April 30, 2026 value (infinity, post-repeal).
        """
        params = uk_system.get_parameters_at_instant("2026-01-15")
        child_limit = params.gov.dwp.universal_credit.elements.child.limit.child_count
        # This returns inf because the whole year 2026 is set to fiscal year value
        assert child_limit == float("inf")

    def test_december_2025_returns_fiscal_year_2025_value(self, uk_system):
        """December 2025 should return fiscal year 2025/26 value."""
        params = uk_system.get_parameters_at_instant("2025-12-15")
        child_limit = params.gov.dwp.universal_credit.elements.child.limit.child_count
        # The year 2025 is set to April 30, 2025 value (2, pre-repeal)
        assert child_limit == 2


class TestMidYearRateChanges:
    """Tests for changes taking effect part-way through a fiscal year.

    Sampling one date per year drops any change taking effect after it.
    Parameters carrying `fiscal_year_blend: true` are day-weighted across
    the year instead.
    """

    # Fiscal year 2024-25 runs 6 April 2024 to 5 April 2025: 207 days at the
    # rates in force before 30 October 2024, then 158 days at the rates after.
    DAYS_BEFORE = 207
    DAYS_AFTER = 158
    TOTAL_DAYS = DAYS_BEFORE + DAYS_AFTER

    def blended(self, before, after):
        return (before * self.DAYS_BEFORE + after * self.DAYS_AFTER) / self.TOTAL_DAYS

    @pytest.mark.parametrize(
        "rate_name, before, after",
        [("basic_rate", 0.10, 0.18), ("higher_rate", 0.20, 0.24)],
    )
    def test_cgt_rates_blend_across_the_split_year(self, rate_name, before, after):
        """2024-25 carries both statutory rates, so the year takes their average."""
        system = CountryTaxBenefitSystem()
        rates = {
            year: getattr(
                system.get_parameters_at_instant(str(year)).gov.hmrc.cgt, rate_name
            )
            for year in (2023, 2024, 2025)
        }

        assert rates[2023] == pytest.approx(before)
        assert rates[2024] == pytest.approx(self.blended(before, after))
        assert rates[2025] == pytest.approx(after)

    def test_cgt_rate_rise_takes_effect_from_the_statutory_date(self):
        """Finance Act 2025 s.7 applies to disposals from 30 October 2024.

        Read before fiscal year conversion, which is what the statutory dates
        feed. Regression test for dating the rise to 6 April 2025, which moved
        a change the legislation makes in 2024-25 into the following year.
        """
        import policyengine_uk
        from pathlib import Path
        from policyengine_core.parameters import ParameterNode

        parameters = ParameterNode(
            directory_path=str(Path(policyengine_uk.__file__).parent / "parameters")
        )
        higher_rate = parameters.gov.hmrc.cgt.higher_rate

        assert higher_rate("2024-10-29") == pytest.approx(0.20)
        assert higher_rate("2024-10-30") == pytest.approx(0.24)

    def test_blending_is_opt_in(self, uk_system):
        """Parameters without the flag keep one sampled value for the year.

        National Insurance rates fell part-way through 2022-23, and the year
        still takes the rate in force at its start rather than an average.
        Whether to blend is a decision per parameter: a transaction is taxed
        at the rate in force on its date, not at a yearly average.
        """
        parameters = uk_system.get_parameters_at_instant("2022")
        employee_rates = parameters.gov.hmrc.national_insurance.class_1.rates.employee

        assert employee_rates.main == pytest.approx(0.1325)


class TestFiscalYearCoverage:
    """Tests to verify fiscal year conversion covers all needed years."""

    @pytest.mark.parametrize("year", [2025, 2026, 2027, 2028, 2029, 2030, 2040])
    def test_year_in_conversion_range(self, uk_system, year):
        """
        Test that years from 2025-2040 can be queried.

        This verifies that the fiscal year conversion range covers
        all years needed for long-term projections.
        """
        params = uk_system.get_parameters_at_instant(str(year))
        assert params is not None
        # Verify we can access a parameter
        pa = params.gov.hmrc.income_tax.allowances.personal_allowance.amount
        assert pa is not None
        assert pa > 0
