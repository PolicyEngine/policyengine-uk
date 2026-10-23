"""Statutory gambling rate dates and fiscal-year reform behaviour."""

import pytest

from policyengine_uk import CountryTaxBenefitSystem, Microsimulation
from policyengine_uk.model_api import Scenario


@pytest.mark.parametrize(
    "path,before,after,old,new",
    [
        ("remote_gaming.rate", "2026-03-31", "2026-04-01", 0.21, 0.4),
        ("general_betting.rates.remote", "2027-03-31", "2027-04-01", 0.15, 0.25),
    ],
)
def test_gambling_rates_preserve_exact_statutory_dates(path, before, after, old, new):
    """Finance Act 2026 sections 86 and 87 change rates on 1 April."""
    system = CountryTaxBenefitSystem()
    rate = system.parameters.get_child(f"gov.hmrc.gambling_duty.{path}")
    assert rate(before) == old
    assert rate(after) == new


def gambling_simulation(year, changes, inputs):
    return Microsimulation(
        situation={
            "people": {"person1": {"age": {year: 40}}},
            "benunits": {"benunit": {"members": ["person1"]}},
            "households": {
                "household": {
                    "members": ["person1"],
                    **{name: {year: value} for name, value in inputs.items()},
                }
            },
        },
        scenario=Scenario(parameter_changes=changes),
    )


@pytest.mark.parametrize(
    "year,path,inputs,variable,expected",
    [
        (
            2025,
            "remote_gaming.rate",
            {"remote_gaming_net_losses": 36_500},
            "remote_gaming_duty",
            18_250,
        ),
        (
            2026,
            "general_betting.rates.remote",
            {"remote_other_betting_net_losses": 36_500},
            "general_betting_duty",
            18_250,
        ),
        (
            2026,
            "machine_games.rates.standard",
            {"machine_games_standard_rate_net_takings": 36_500},
            "machine_games_duty",
            18_250,
        ),
    ],
)
def test_annual_gambling_reform_replaces_the_whole_fiscal_year(
    year, path, inputs, variable, expected
):
    """A 50% annual reform applies to all GBP 36,500 of the year's base."""
    sim = gambling_simulation(
        year, {f"gov.hmrc.gambling_duty.{path}": {str(year): 0.5}}, inputs
    )
    assert sim.calculate(variable, year).values[0] == pytest.approx(expected)


def test_explicit_date_reform_keeps_its_dates_and_adjacent_fiscal_year():
    """Five days at 50%, 360 at 15%, then the FY2026 statutory transition."""
    sim = gambling_simulation(
        2025,
        {
            "gov.hmrc.gambling_duty.general_betting.rates.remote": {
                "2026-04-01.2026-04-05": 0.5
            }
        },
        {"remote_other_betting_net_losses": 36_500},
    )
    sim.set_input("remote_other_betting_net_losses", 2026, [36_500])
    # Explicit five-day reform: 100 * (360 * .15 + 5 * .50).
    assert sim.calculate("general_betting_duty", 2025).values[0] == pytest.approx(5_650)
    # Finance Act 2026 section 87: 100 * (360 * .15 + 5 * .25).
    assert sim.calculate("general_betting_duty", 2026).values[0] == pytest.approx(5_525)
