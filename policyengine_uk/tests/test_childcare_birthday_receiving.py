"""Receiving flags follow positive native awards in actual funded terms.

DfE guidance effective 1 April 2026 A1.2/A1.4/A1.7 and SI2014/2147 reg3
allow both annual base awards in different terms of a transition year.
https://www.gov.uk/government/publications/early-education-and-childcare--2/early-education-and-childcare-valid-from-1-april-2026
https://www.legislation.gov.uk/uksi/2014/2147/regulation/3

The existing equal-third annual valuation uses 190 base hours per term at
2026 national-average proxies: £8.90 for targeted and £6.61 for universal.
These tests do not import internal term helpers. Supplied annual amounts or
shares preserve their original snapshot-age receiving predicates.
"""

from datetime import date

import pytest

from policyengine_uk import Simulation

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")
YEAR = 2026
U = "universal_childcare_entitlement"
T = "targeted_childcare_entitlement"
RU = "is_child_receiving_universal_childcare"
RT = "is_child_receiving_targeted_childcare"


def simulation(
    born, *, country="ENGLAND", targeted=True, claim=True, annual=None, reform=None
):
    age = YEAR - born.year - ((10, 6) < (born.month, born.day))
    child = {"age": {YEAR: age}, "date_of_birth": {YEAR: int(born.strftime("%Y%m%d"))}}
    child.update({name: {YEAR: value} for name, value in (annual or {}).items()})
    return Simulation(
        situation={
            "people": {"child": child},
            "benunits": {
                "family": {
                    "members": ["child"],
                    "targeted_childcare_entitlement_eligible": {YEAR: targeted},
                    "extended_childcare_entitlement_eligible": {YEAR: False},
                    "would_claim_universal_childcare": {YEAR: claim},
                    "would_claim_targeted_childcare": {YEAR: claim},
                }
            },
            "households": {"home": {"members": ["child"], "country": {YEAR: country}}},
        },
        reform=reform,
    )


def amount(sim, variable):
    return float(sim.calculate(variable, YEAR)[0])


def receiving(sim, variable):
    return bool(sim.calculate(variable, YEAR)[0])


@pytest.mark.parametrize(
    "born,award,flag,expected",
    [
        (date(2023, 10, 7), U, RU, 1255.90),
        (date(2024, 10, 7), T, RT, 1691.00),
        (date(2023, 8, 31), T, RT, 1691.00),
        (date(2023, 9, 1), U, RU, 1255.90),
    ],
)
def test_receiving_follows_a_positive_native_birthday_term(born, award, flag, expected):
    sim = simulation(born)
    assert amount(sim, award) == pytest.approx(expected, abs=0.01)
    assert receiving(sim, flag)


def test_transition_year_receives_both_programmes_in_disjoint_terms():
    sim = simulation(date(2023, 8, 31))
    # Targeted April, universal September and January; not double funding.
    assert amount(sim, T) == pytest.approx(1691, abs=0.01)
    assert amount(sim, U) == pytest.approx(2511.80, abs=0.01)
    assert receiving(sim, RT)
    assert receiving(sim, RU)


@pytest.mark.parametrize(
    "born,award,flag",
    [
        (date(2025, 1, 1), T, RT),
        (date(2024, 1, 1), U, RU),
    ],
)
def test_a_birthday_on_the_last_term_start_does_not_create_receipt(born, award, flag):
    sim = simulation(born)
    assert amount(sim, award) == 0
    assert not receiving(sim, flag)


@pytest.mark.parametrize(
    "born,country,targeted",
    [
        (date(2023, 10, 7), "WALES", False),
        (date(2021, 4, 6), "ENGLAND", True),
    ],
)
def test_region_and_school_age_guards_still_prevent_receipt(born, country, targeted):
    sim = simulation(born, country=country, targeted=targeted)
    assert amount(sim, U) == amount(sim, T) == 0
    assert not receiving(sim, RU)
    assert not receiving(sim, RT)


@pytest.mark.parametrize(
    "born,award,flag",
    [
        (date(2023, 10, 7), U, RU),
        (date(2023, 8, 31), T, RT),
        (date(2021, 4, 6), U, RU),
    ],
)
def test_supplied_positive_annual_amount_keeps_original_age_guard(born, award, flag):
    sim = simulation(born, annual={award: 1000})
    assert amount(sim, award) == 1000
    assert not receiving(sim, flag)


def test_non_third_legacy_share_keeps_snapshot_receiving_semantics():
    sim = simulation(
        date(2023, 10, 7), annual={"early_years_term_share_before_school": 0.4}
    )
    assert amount(sim, U) == 0
    assert amount(sim, T) == pytest.approx(5073, abs=0.01)
    assert not receiving(sim, RU)
    assert receiving(sim, RT)


def test_independent_universal_reform_does_not_erase_targeted_term_receipt():
    sim = simulation(
        date(2023, 8, 31), reform={"gov.dfe.universal_childcare_entitlement.age.min": 4}
    )
    assert amount(sim, U) == 0
    assert amount(sim, T) == pytest.approx(1691, abs=0.01)
    assert not receiving(sim, RU)
    assert receiving(sim, RT)


def test_legal_term_eligibility_without_take_up_does_not_create_receipt():
    sim = simulation(date(2023, 8, 31), claim=False)
    assert amount(sim, U) == amount(sim, T) == 0
    assert not receiving(sim, RU)
    assert not receiving(sim, RT)


def test_reformed_universal_upper_age_guard_stays_independent():
    sim = simulation(
        date(2023, 10, 7), reform={"gov.dfe.universal_childcare_entitlement.age.max": 2}
    )
    assert amount(sim, U) == 0
    assert not receiving(sim, RU)
