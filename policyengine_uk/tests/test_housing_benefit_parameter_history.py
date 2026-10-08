"""Externally sourced Housing Benefit threshold history and citation checks."""

from pathlib import Path

import pytest
from policyengine_core.parameters import ParameterNode

from policyengine_uk.system import system


@pytest.fixture(scope="module")
def written_housing_benefit_parameters():
    """Read statutory dates before the model's fiscal-year conversion."""
    directory = (
        Path(__file__).parents[1] / "parameters" / "gov" / "dwp" / "housing_benefit"
    )
    return ParameterNode(directory_path=str(directory))


@pytest.mark.parametrize(
    "date, expected",
    [
        # SI 2006/214 reg 29(2)(b), outside its accommodation exception.
        ("2006-04-10", 6_000),
        ("2008-04-30", 6_000),
        ("2009-11-01", 6_000),
        # SI 2009/1676 regs 1 and 5; NI SR 2009/262 regs 1 and 3.
        ("2009-11-02", 10_000),
        ("2009-11-03", 10_000),
        ("2015-04-30", 10_000),
        ("2026-04-30", 10_000),
    ],
)
def test_written_standard_pension_capital_threshold(
    written_housing_benefit_parameters, date, expected
):
    threshold = written_housing_benefit_parameters.means_test.capital.pension_age.tariff_income.threshold
    assert threshold(date) == expected


@pytest.mark.parametrize("year", [2015, 2025, 2026])
def test_supported_model_year_thresholds_are_unchanged(year):
    """The historical correction must not alter supported-year thresholds."""
    capital = system.parameters(str(year)).gov.dwp.housing_benefit.means_test.capital
    assert capital.pension_age.tariff_income.threshold == 10_000
    assert capital.working_age.tariff_income.threshold == 6_000


@pytest.mark.parametrize("year", [2015, 2019, 2026])
def test_allowance_age_constants_remain_available_in_supported_years(year):
    """Existing package backdating supplies the age constants before 2019."""
    ages = system.parameters(str(year)).gov.dwp.housing_benefit.allowances.age_threshold
    # SI 2006/213 Sch 3 Part 1 para 1; NI SR 2006/405 Sch 4 Part I.
    assert ages.older == 25
    assert ages.younger == 18


@pytest.mark.parametrize("name", ["older", "younger"])
def test_allowance_age_references_identify_the_allowance_schedules(
    written_housing_benefit_parameters, name
):
    age = getattr(written_housing_benefit_parameters.allowances.age_threshold, name)
    references = {reference["href"] for reference in age.metadata["reference"]}
    assert references == {
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3/part/1/made",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/4",
    }


@pytest.mark.parametrize(
    "date, expected_references",
    [
        (
            "2006-04-10",
            {
                "https://www.legislation.gov.uk/uksi/2006/214/regulation/29/made",
                "https://www.legislation.gov.uk/nisr/2006/406/regulation/27/made",
            },
        ),
        (
            "2009-11-02",
            {
                "https://www.legislation.gov.uk/uksi/2009/1676/made",
                "https://www.legislation.gov.uk/nisr/2009/262/made",
            },
        ),
    ],
)
def test_pension_capital_values_have_dated_gb_and_ni_sources(
    written_housing_benefit_parameters, date, expected_references
):
    threshold = written_housing_benefit_parameters.means_test.capital.pension_age.tariff_income.threshold
    values = {value.instant_str: value for value in threshold.values_list}
    assert date in values
    references = {reference["href"] for reference in values[date].metadata["reference"]}
    assert references == expected_references
