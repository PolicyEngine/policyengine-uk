"""Tests for the Scottish Child Payment baby bonus contrib reform.

The £40/week rate for under-1s was announced in the Scottish Budget 2026-27 but
is not in legislation: SSI 2026/170 reg 8 sets a single flat rate with no
under-1 tier. It must therefore stay out of the baseline and only apply when a
reform switches ``gov.contrib.scotland.scottish_child_payment.in_effect`` on.

The comparisons below use the ordinary rate for the year, whatever that is:
only the 2026-27 figure of GBP 28.20 is set by regulation, while later years
are uprated forecasts. The tests assert that an under-1 is paid the same rate
as an older child, so they hold whatever those later figures become.

Same class of defect as issue #1852, which covers the Two Child Limit Payment.
"""

import pytest

from policyengine_uk import Simulation
from policyengine_uk.utils.scenario import Scenario

IN_EFFECT = "gov.contrib.scotland.scottish_child_payment.in_effect"


def situation(year: int) -> dict:
    return {
        "people": {
            "parent": {"age": {year: 30}},
            "baby": {"age": {year: 0}},
            "child": {"age": {year: 5}},
        },
        "benunits": {
            "benunit": {
                "members": ["parent", "baby", "child"],
                "universal_credit": {year: 5_000},
            }
        },
        "households": {
            "household": {
                "members": ["parent", "baby", "child"],
                "region": {year: "SCOTLAND"},
            }
        },
    }


def scp(year: int, scenario: Scenario = None) -> list:
    simulation = Simulation(situation=situation(year), scenario=scenario)
    return list(simulation.calculate("scottish_child_payment", year))


@pytest.mark.parametrize("year", [2026, 2027, 2028])
def test_baby_bonus_not_in_baseline(year: int):
    """Under-1s get the same ordinary rate as older children in the baseline."""
    _, baby, child = scp(year)

    assert baby == pytest.approx(child, abs=1e-2), (
        f"In {year} an under-1 received {baby:,.2f} against {child:,.2f} for a "
        "5-year-old: the SCP baby bonus is leaking into the baseline."
    )


def test_baby_bonus_applies_when_switched_on():
    """A reform setting `in_effect` still raises the under-1 rate to £40/week."""
    scenario = Scenario(
        applied_before_data_load=True,
        parameter_changes={IN_EFFECT: True},
    )
    _, baby, child = scp(2027, scenario)

    # £40.00/week * 52 weeks vs the £28.85/week ordinary rate * 52 weeks.
    assert baby == pytest.approx(2_080, abs=10)
    assert child == pytest.approx(1_500, abs=10)
