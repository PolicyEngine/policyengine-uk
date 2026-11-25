"""Statutory and annual boundaries for Scottish CTR looked-after placements."""

from pathlib import Path

import policyengine_uk
import pytest
from policyengine_core.parameters import ParameterNode
from policyengine_uk import CountryTaxBenefitSystem


@pytest.fixture(scope="module")
def raw_looked_after_exclusion():
    """Read the dated YAML before fiscal-year conversion changes its timeline."""
    parameters = ParameterNode(
        directory_path=str(Path(policyengine_uk.__file__).parent / "parameters")
    )
    working_age = (
        parameters.gov.local_authorities.scotland.council_tax_reduction.working_age
    )
    return working_age.looked_after_exclusion_is_foster_only


@pytest.mark.parametrize(
    "date, expected",
    [
        ("2022-04-01", False),
        ("2024-10-30", False),
        ("2024-10-31", True),
    ],
)
def test_foster_only_exclusion_starts_on_statutory_date(
    raw_looked_after_exclusion, date, expected
):
    """SSI 2024/230 regs. 1 and 3 amend reg. 7(8) on 31 October 2024."""
    assert raw_looked_after_exclusion(date) == expected


@pytest.fixture(scope="module")
def uk_system():
    return CountryTaxBenefitSystem()


@pytest.mark.parametrize(
    "date, expected",
    [
        ("2022-01-01", False),
        ("2023-01-01", False),
        ("2024-01-01", False),
        ("2024-12-31", False),
        ("2025-01-01", True),
        ("2026-01-01", True),
    ],
)
def test_annual_rule_uses_the_existing_april_sampling(uk_system, date, expected):
    """Annual 2024 samples before the amendment; annual 2025 samples after it.

    Ordinary government parameters take their 30 April value for the whole
    calendar-labelled year. This preserves that approximation without moving
    the raw statutory commencement date or introducing an intrayear split.
    """
    parameters = uk_system.get_parameters_at_instant(date)
    working_age = (
        parameters.gov.local_authorities.scotland.council_tax_reduction.working_age
    )
    assert working_age.looked_after_exclusion_is_foster_only == expected
