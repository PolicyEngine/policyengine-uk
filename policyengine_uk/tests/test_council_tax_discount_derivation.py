"""The no-resident council tax discount must derive from the appropriate percentage.

LGFA 1992 s.11(2) sets the no-resident discount as "twice the appropriate
percentage", and s.11(3) sets the appropriate percentage at 25 per cent unless
the Secretary of State orders otherwise. The familiar 50 per cent is therefore
derived, not a printed statutory figure. These tests change the appropriate
percentage and assert that both rates move with it, which a hardcoded 0.5 would
fail.
"""

from policyengine_uk import Simulation

YEAR = 2026

PARAMETER = "gov.local_authorities.council_tax.discounts.appropriate_percentage.england"

SINGLE_ADULT = {
    "people": {"person": {"age": {YEAR: 40}}},
    "benunits": {"benunit": {"members": ["person"]}},
    "households": {
        "household": {
            "members": ["person"],
            "region": {YEAR: "SOUTH_EAST"},
            "local_authority": {YEAR: "MAIDSTONE"},
            "council_tax_band": {YEAR: "D"},
        }
    },
}

NO_RESIDENT = {
    "people": {"person": {"age": {YEAR: 10}}},
    "benunits": {"benunit": {"members": ["person"]}},
    "households": {
        "household": {
            "members": ["person"],
            "region": {YEAR: "SOUTH_EAST"},
            "local_authority": {YEAR: "MAIDSTONE"},
            "council_tax_band": {YEAR: "D"},
        }
    },
}


def _rate(situation, reform=None):
    simulation = Simulation(situation=situation, reform=reform)
    return simulation.calculate("council_tax_discount_rate", YEAR)[0]


def test_baseline_rates_are_the_statutory_defaults():
    assert _rate(SINGLE_ADULT) == 0.25
    assert _rate(NO_RESIDENT) == 0.5


def test_no_resident_rate_is_twice_the_appropriate_percentage():
    reform = {PARAMETER: {f"{YEAR}-01-01.{YEAR}-12-31": 0.3}}
    assert _rate(SINGLE_ADULT, reform) == 0.3
    # Twice the appropriate percentage, not an independently set 0.5.
    assert abs(_rate(NO_RESIDENT, reform) - 0.6) < 1e-9


def test_zero_appropriate_percentage_removes_both_discounts():
    reform = {PARAMETER: {f"{YEAR}-01-01.{YEAR}-12-31": 0}}
    assert _rate(SINGLE_ADULT, reform) == 0
    assert _rate(NO_RESIDENT, reform) == 0
