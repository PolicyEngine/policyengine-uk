"""ITA 2007 s21(3A): annual savings limit, September CPI and £10 ceilings.

The £5,000 freeze ends in 2030-31 (FA 2026 s9). Future CPI in these
tests is an explicit scenario assumption, not a statutory future amount.
Savings-only income avoids the separately tracked starter-band taper #1799.
"""

from decimal import Decimal
from pathlib import Path

import numpy as np
import pytest
import yaml
from policyengine_core.reforms import Reform

import policyengine_uk
from policyengine_uk import CountryTaxBenefitSystem, Simulation
from policyengine_uk.parameters.gov.economic_assumptions.create_economic_assumption_indices import (
    growth_horizon,
)
from policyengine_uk.parameters.gov.hmrc import create_threshold_indexation
from policyengine_uk.utils.scenario import Scenario

LIMIT = "gov.hmrc.income_tax.rates.savings_starter_rate.allowance"
CPI = "gov.economic_assumptions.statutory_uprating_inputs.cpi_september"
PA = "gov.hmrc.income_tax.allowances.personal_allowance.amount"
PARAMETER_FILE = (
    Path(policyengine_uk.__file__).parent
    / "parameters/gov/hmrc/income_tax/rates/savings_starter_rate/allowance.yaml"
)


@pytest.fixture(scope="module")
def system():
    return CountryTaxBenefitSystem()


def limit(system, year, baseline=False):
    root = system.parameters.baseline if baseline else system.parameters
    return root.get_child(LIMIT)(f"{year}-01-01")


def with_cpi(system, rates):
    result = system.clone()
    result.reset_parameters()
    parameter = result.parameters.get_child(CPI)
    for year, rate in rates.items():
        parameter.update(period=f"year:{year}-09-01:1", value=rate)
    result.process_parameters()
    return result


@pytest.mark.parametrize("year", range(2026, 2031))
def test_starting_rate_limit_is_frozen_through_2030(system, year):
    assert limit(system, year) == 5_000


def test_starting_rate_limit_has_annual_metadata_without_double_uprating():
    metadata = yaml.safe_load(PARAMETER_FILE.read_text())["metadata"]
    assert metadata["period"] == "year"
    assert "uprating" not in metadata


@pytest.mark.parametrize(
    "previous,increase,expected",
    [
        (5_000, "0.02", 5_100),
        (5_100, "0.02", 5_210),
        (5_210, "0.02", 5_320),
        (5_000, "0.001", 5_010),
        (5_000, "0.002", 5_010),
        (5_000, "0", 5_000),
        (5_100, "-0.01", 5_100),
    ],
)
def test_starting_rate_statutory_rounding(previous, increase, expected):
    assert create_threshold_indexation.index_savings_starting_rate_limit(
        Decimal(previous), Decimal(increase)
    ) == Decimal(expected)


def test_starting_rate_uses_the_previous_rounded_annual_limit(system):
    indexed = with_cpi(system, dict.fromkeys(range(2030, 2039), 0.02))
    for year, expected in [(2030, 5_000), (2031, 5_100), (2032, 5_210), (2033, 5_320)]:
        assert limit(indexed, year) == expected
        if year > 2030:
            assert limit(indexed, year, baseline=True) == expected
    horizon = growth_horizon(indexed.parameters.gov.economic_assumptions.yoy_growth)
    assert limit(indexed, horizon) > limit(indexed, 2040) > limit(indexed, 2039)
    assert limit(indexed, horizon + 1) == limit(indexed, horizon)
    # Reapplying the helper does not append another year's increase.
    create_threshold_indexation.add_threshold_indexation(indexed.parameters)
    assert limit(indexed, 2031) == 5_100


@pytest.mark.parametrize("rate", [0, -0.01])
def test_nonpositive_cpi_preserves_the_preceding_limit(system, rate):
    indexed = with_cpi(system, {2030: 0.02, 2031: rate})
    assert limit(indexed, 2031) == 5_100
    assert limit(indexed, 2032) == 5_100


def savings_situation():
    years = range(2030, 2034)
    return {
        "people": {
            "saver": {
                "age": {year: 40 for year in years},
                "savings_interest_income": {year: 20_000 for year in years},
            }
        },
        "benunits": {"benunit": {"members": ["saver"]}},
        "households": {
            "household": {
                "members": ["saver"],
                "region": {year: "LONDON" for year in years},
            }
        },
    }


@pytest.mark.parametrize("route", ["dict", "parameter_changes", "Reform.from_dict"])
def test_indexed_starting_rate_reaches_final_savings_income_tax(route):
    # Hold the PA at £12,570 to isolate this band's effect. With £20,000
    # interest and the unchanged £1,000 PSA, £6,430 remains before the
    # starting rate. The basic savings rate from 2027-28 is 24% (22% from
    # Budget 2025 plus 2 points from Budget 2026).
    changes = {
        CPI: {"2030-09-01.2038-08-31": 0.02},
        PA: {"2030-04-06.2034-04-05": 12_570},
    }
    if route == "parameter_changes":
        simulation = Simulation(
            situation=savings_situation(),
            scenario=Scenario(parameter_changes=changes),
        )
    else:
        reform = changes if route == "dict" else Reform.from_dict(changes)
        simulation = Simulation(situation=savings_situation(), reform=reform)
    for year, starter, tax in [
        (2030, 5_000, 343.20),
        (2031, 5_100, 319.20),
        (2032, 5_210, 292.80),
        (2033, 5_320, 266.40),
    ]:
        assert simulation.calculate("personal_allowance", year)[0] == 12_570
        assert simulation.calculate("savings_allowance", year)[0] == 1_000
        assert simulation.calculate("savings_starter_rate_income", year)[0] == starter
        np.testing.assert_allclose(
            simulation.calculate("savings_income_tax", year), [tax], rtol=0, atol=0.001
        )
        np.testing.assert_allclose(
            simulation.calculate("income_tax", year), [tax], rtol=0, atol=0.001
        )


def savings_simulation(route, changes):
    if route == "parameter_changes":
        return Simulation(
            situation=savings_situation(),
            scenario=Scenario(parameter_changes=changes),
        )
    reform = changes if route == "dict" else Reform.from_dict(changes)
    return Simulation(situation=savings_situation(), reform=reform)


@pytest.mark.parametrize("route", ["dict", "parameter_changes", "Reform.from_dict"])
def test_dated_limit_override_resumes_indexation_from_the_changed_limit(route):
    # ITA 2007 s21(3A) uses the previous year's limit, including a reform's
    # £6,000, then rounds the 2% increase up to £10: £6,120 in 2032.
    # The separately constructed CPI/PA-only control retains its own path.
    changes = {
        CPI: {"2030-09-01.2038-08-31": 0.02},
        PA: {"2030-04-06.2034-04-05": 12_570},
    }
    control = savings_simulation(route, changes)
    simulation = savings_simulation(
        route, {**changes, LIMIT: {"2031-04-06.2032-04-05": 6_000}}
    )
    assert limit(simulation.tax_benefit_system, 2030) == 5_000
    assert limit(simulation.tax_benefit_system, 2031) == 6_000
    assert limit(simulation.tax_benefit_system, 2032) == 6_120
    assert limit(control.tax_benefit_system, 2032) == 5_210
    # With genuine £20,000 interest, the held PA and natural PSA leave
    # £6,430 before the starting rate: (6,430 - limit) x 24%.
    for current, year, tax in [
        (simulation, 2031, 103.20),
        (simulation, 2032, 74.40),
        (control, 2032, 292.80),
    ]:
        assert current.calculate("personal_allowance", year)[0] == 12_570
        assert current.calculate("savings_allowance", year)[0] == 1_000
        for variable in ("savings_income_tax", "income_tax"):
            np.testing.assert_allclose(
                current.calculate(variable, year), [tax], rtol=0, atol=0.001
            )


@pytest.mark.parametrize(
    "start,stop,expected",
    [
        ("2029-04-06", "2030-04-29", (6_000, 5_000, 5_100, 5_210)),
        ("2029-04-06", "2030-04-30", (6_000, 6_000, 6_120, 6_250)),
        ("2030-04-06", "2030-04-29", (5_000, 5_000, 5_100, 5_210)),
    ],
)
def test_override_replacing_the_last_file_value_keeps_uncovered_years(
    start, stop, expected
):
    # The file's last anchor is 2030-04-06. Replacing it must retain the
    # stated 2030 freeze when the change ends before the 30 April sample.
    # A change covering that sample instead supplies the previous-year
    # base for 2031; £6,120 x 1.02 then ceilings to £6,250 for 2032.
    simulation = savings_simulation(
        "dict",
        {
            CPI: {"2030-09-01.2038-08-31": 0.02},
            LIMIT: {f"{start}.{stop}": 6_000},
        },
    )
    assert [
        limit(simulation.tax_benefit_system, year) for year in range(2029, 2033)
    ] == list(expected)


def test_reset_and_reprocessing_keep_the_changed_savings_indexation_path():
    simulation = savings_simulation(
        "dict",
        {
            CPI: {"2030-09-01.2038-08-31": 0.02},
            PA: {"2030-04-06.2034-04-05": 12_570},
            LIMIT: {"2031-04-06.2032-04-05": 6_000},
        },
    )
    system = simulation.tax_benefit_system
    assert limit(system, 2032) == 6_120
    system.reset_parameters()
    system.reset_parameters()
    system.process_parameters()
    assert [limit(system, year) for year in range(2030, 2033)] == [
        5_000,
        6_000,
        6_120,
    ]
    assert system._parameters_before_reset is None
    # Calculate after rebuilding, so this is not a cached pre-reset award.
    assert simulation.calculate("personal_allowance", 2032)[0] == 12_570
    assert simulation.calculate("savings_allowance", 2032)[0] == 1_000
    for variable in ("savings_income_tax", "income_tax"):
        np.testing.assert_allclose(
            simulation.calculate(variable, 2032), [74.40], rtol=0, atol=0.001
        )
