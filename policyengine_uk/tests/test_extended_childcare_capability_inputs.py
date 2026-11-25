"""Childcare requires supplied current capability status, including treated-as status.

SI 2022/1134 reg 4 adopts UC Regulations 2013 regs 39/40. Childcare regs
14(4)(b)(i)-(ii) and 15(4)(a)-(b) admit either status with a working partner.
The childcare input contract accepts a status supplied for the requested year;
a disability proxy, calculated cache or earlier year's input does not supply it.
Missing status uses a conservative model default and remains legally unknown.
"""

import pytest
from policyengine_core.periods import period

from policyengine_uk import Simulation
from policyengine_uk.utils.supplied_inputs import is_supplied_input

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

YEAR = 2025
LCW = "uc_limited_capability_for_work"
LCWRA = "uc_limited_capability_for_WRA"
ELIGIBLE = "extended_childcare_entitlement_eligible"


def proxy_family(years=(YEAR,)):
    """An England child aged 4, a working parent, and a nonworking PIP recipient.

    At the supplied minimum wage, quarterly earnings of 5,000 exceed the
    reg 18 minimum of 16 * 10 * 13 = 2,080. Every specified benefit is absent.
    Omit both capability inputs from every person, so the situation builder
    cannot create supplied false arrays that mask the nonworker's fallback.
    """

    def annual(value):
        return {year: value for year in years}

    absent_benefits = {
        name: annual(value)
        for name, value in {
            "is_entitled_to_carer_benefit": False,
            "receives_uc_carer_element": False,
            "receives_limited_capability_for_work_credits": False,
            "esa_contrib": 0,
            "incapacity_benefit": 0,
            "sda": 0,
        }.items()
    }
    members = ["person1", "person2", "person3"]
    return Simulation(
        situation={
            "people": {
                "person1": {
                    "age": annual(40),
                    "is_parent": annual(True),
                    "employment_income": annual(20_000),
                    "adjusted_net_income": annual(20_000),
                    "minimum_wage": annual(10),
                    **absent_benefits,
                },
                "person2": {
                    "age": annual(38),
                    "is_parent": annual(True),
                    "employment_income": annual(0),
                    "adjusted_net_income": annual(0),
                    "minimum_wage": annual(10),
                    "is_disabled_for_benefits": annual(True),
                    "pip": annual(1_000),
                    "dla": annual(0),
                    **absent_benefits,
                },
                "person3": {"age": annual(4)},
            },
            "benunits": {
                "benunit": {
                    "members": members,
                    "would_claim_extended_childcare": annual(True),
                    "claimant_or_partner_esa_income": annual(0),
                }
            },
            "households": {
                "household": {"members": members, "country": annual("ENGLAND")}
            },
        }
    )


def test_warmed_uc_capability_defaults_do_not_supply_childcare_status():
    """Warming the unchanged global disability fallbacks cannot establish status."""
    simulation = proxy_family()
    person = simulation.populations["person"]
    for capability in (LCWRA, LCW):
        value = simulation.calculate(capability, YEAR)
        assert value.tolist() == [False, True, False]
        assert not is_supplied_input(person, capability, period(YEAR), value)

    assert simulation.calculate(ELIGIBLE, YEAR).tolist() == [False]


@pytest.mark.parametrize("capability", [LCW, LCWRA])
def test_equal_capability_values_qualify_only_when_supplied(capability):
    """An entered current determination can equal a proxy without sharing its source."""
    simulation = proxy_family()
    person = simulation.populations["person"]
    derived = simulation.calculate(capability, YEAR).copy()
    assert derived.tolist() == [False, True, False]
    assert not is_supplied_input(person, capability, period(YEAR), derived)
    assert simulation.calculate(ELIGIBLE, YEAR).tolist() == [False]

    # The caller now supplies the same values as current determined/treated-as
    # status. Public set_input records the changed source, despite equal values.
    simulation.set_input(capability, YEAR, derived)
    supplied = simulation.calculate(capability, YEAR)
    assert supplied.tolist() == derived.tolist()
    assert is_supplied_input(person, capability, period(YEAR), supplied)
    assert simulation.calculate(ELIGIBLE, YEAR).tolist() == [True]


def test_previous_year_status_does_not_supply_current_year_status():
    """An annual status input needs renewal even while the global proxy stays true."""
    next_year = YEAR + 1
    simulation = proxy_family(years=(YEAR, next_year))
    simulation.set_input(LCW, YEAR, [False, True, False])
    person = simulation.populations["person"]
    assert simulation.calculate(ELIGIBLE, YEAR).tolist() == [True]

    current_value = simulation.calculate(LCW, next_year)
    assert current_value.tolist() == [False, True, False]
    assert not is_supplied_input(person, LCW, period(next_year), current_value)
    assert simulation.calculate(ELIGIBLE, next_year).tolist() == [False]

    simulation.set_input(LCW, next_year, [False, True, False])
    current_value = simulation.calculate(LCW, next_year)
    assert is_supplied_input(person, LCW, period(next_year), current_value)
    assert simulation.calculate(ELIGIBLE, next_year).tolist() == [True]
