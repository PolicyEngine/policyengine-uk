"""Property-based tests: the Universal Credit renter exemption from housing cost
contributions follows the claimants and reg 2's attendance allowance.

Under UC Regs 2013 Sch 4 para 15(1), the Secretary of State makes no deduction
under para 13 for a renter who is a single person, or a joint renter where at
least one joint renter is a person, to whom para 15(2) applies. Para 1(2) calls
the claimants "renters" and joint claimants "joint renters". Where a member of
a couple claims as a single person under reg 3(3), the other member is neither.
Para 15(2)(c) names "a person in receipt of attendance allowance", which reg 2
defines to include armed forces independence payment (head (f)).

Each generated household has a claimant aged 18 to 64 who heads the household
and rents, a partner whom `uc_is_ineligible_partner` flags (so the claimant
claims as a single person), an adult son in their benefit unit, and an adult
non-dependant in a family of their own that makes no claim. Invariants:

1. Making the flagged partner blind, or giving them Attendance Allowance, armed
   forces independence payment, the middle or highest rate of the DLA care
   component or the PIP daily living component, in any combination, never
   changes any family's Universal Credit non-dependant deductions.
2. Giving the single claimant a positive armed forces independence payment
   always exempts the claim and removes its non-dependant deductions.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

YEAR = 2026
SLOTS = 8
ROLES = ["claimant", "partner", "son", "lodger"]
TENURES = ["RENT_FROM_COUNCIL", "RENT_FROM_HA", "RENT_PRIVATELY"]
REGIONS = ["NORTH_WEST", "LONDON", "SCOTLAND", "WALES"]
PROPERTY_SETTINGS = settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
DLA_CATEGORIES = ["NONE", "LOWER", "MIDDLE", "HIGHER"]


def situation():
    people, benunits, households = {}, {}, {}
    for i in range(SLOTS):
        names = {role: f"{role}_{i}" for role in ROLES}
        for role, name in names.items():
            people[name] = {
                "age": {YEAR: 40},
                "is_household_head": {YEAR: role == "claimant"},
                "is_claimant_or_partner": {YEAR: role != "son"},
                "current_education": {YEAR: "NOT_IN_EDUCATION"},
                "employment_income": {YEAR: 0},
            }
        people[names["partner"]]["uc_is_ineligible_partner"] = {YEAR: True}
        benunits[f"family_{i}"] = {
            "members": [names["claimant"], names["partner"], names["son"]],
            "would_claim_uc": {YEAR: True},
        }
        benunits[f"lodger_family_{i}"] = {
            "members": [names["lodger"]],
            "would_claim_uc": {YEAR: False},
        }
        households[f"household_{i}"] = {
            "members": list(names.values()),
            "rent": {YEAR: 6_000},
            "tenure_type": {YEAR: TENURES[i % len(TENURES)]},
            "region": {YEAR: REGIONS[i % len(REGIONS)]},
        }
    return {"people": people, "benunits": benunits, "households": households}


@pytest.fixture(scope="module")
def simulation(cloned_uk_tax_benefit_system):
    return Simulation(situation=situation())


money = st.floats(0, 40_000, allow_nan=False)
# The model holds amounts as 32-bit floats; positive amounts start at a penny.
positive = st.floats(0.01, 20_000, allow_nan=False)
dla_category = st.sampled_from(DLA_CATEGORIES)


@st.composite
def claimant_benefits(draw):
    """Any mix of the para 15(2) qualifications, possibly none."""
    return dict(
        is_blind=draw(st.booleans()),
        attendance_allowance=draw(st.one_of(st.just(0.0), positive)),
        armed_forces_independence_payment=draw(st.one_of(st.just(0.0), positive)),
        dla_sc_category=draw(dla_category),
        pip_dl=draw(st.one_of(st.just(0.0), positive)),
    )


@st.composite
def household(draw):
    return dict(
        claimant_age=draw(st.integers(18, 64)),
        claimant_earnings=draw(st.one_of(st.just(0.0), money)),
        claimant=draw(st.one_of(st.just(NO_BENEFITS), claimant_benefits())),
        partner_age=draw(st.integers(18, 64)),
        partner=draw(claimant_benefits()),
        son_age=draw(st.integers(16, 64)),
        son_earnings=draw(st.one_of(st.just(0.0), money)),
        lodger_age=draw(st.integers(18, 64)),
        lodger_earnings=draw(st.one_of(st.just(0.0), money)),
        rent=draw(st.one_of(st.floats(0, 2_000), st.floats(2_000, 20_000))),
        afip=draw(positive),
    )


NO_BENEFITS = dict(
    is_blind=False,
    attendance_allowance=0.0,
    armed_forces_independence_payment=0.0,
    dla_sc_category="NONE",
    pip_dl=0.0,
)
EVERY_BENEFIT = dict(
    is_blind=True,
    attendance_allowance=5_000.0,
    armed_forces_independence_payment=5_000.0,
    dla_sc_category="HIGHER",
    pip_dl=5_000.0,
)
populations = st.lists(household(), min_size=SLOTS, max_size=SLOTS)


def review_household(partner):
    """The 2026 Maidstone-style household: claimant aged 45, a partner aged 43
    whom reg 3(3) excludes, an ordinary son aged 22 and 10,400 of rent."""
    return dict(
        claimant_age=45,
        claimant_earnings=0.0,
        claimant=NO_BENEFITS,
        partner_age=43,
        partner=partner,
        son_age=22,
        son_earnings=0.0,
        lodger_age=30,
        lodger_earnings=0.0,
        rent=10_400.0,
        afip=5_000.0,
    )


def per_person(households, key):
    """A person array of one input, from each role's own value."""
    values = []
    for h in households:
        values += [
            h["claimant"][key],
            h["partner"][key],
            NO_BENEFITS[key],
            NO_BENEFITS[key],
        ]
    return values


def calculate(sim, households, partner_benefits=True, claimant_afip=False):
    ages, earnings = [], []
    for h in households:
        ages += [h["claimant_age"], h["partner_age"], h["son_age"], h["lodger_age"]]
        earnings += [
            h["claimant_earnings"],
            0.0,
            h["son_earnings"],
            h["lodger_earnings"],
        ]
    sim.set_input("age", YEAR, np.array(ages))
    sim.set_input("employment_income", YEAR, np.array(earnings, dtype=float))
    sim.set_input("rent", YEAR, np.array([h["rent"] for h in households]))
    for key in NO_BENEFITS:
        values = per_person(households, key)
        if not partner_benefits:
            values[1::4] = [NO_BENEFITS[key]] * len(households)
        if key == "armed_forces_independence_payment" and claimant_afip:
            values[0::4] = [h["afip"] for h in households]
        if key == "dla_sc_category":
            sim.set_input(key, YEAR, np.array(values))
        else:
            sim.set_input(key, YEAR, np.array(values, dtype=type(values[0])))
    sim.drop_computed_arrays()
    return {
        name: np.asarray(sim.calculate(name, YEAR))
        for name in [
            "uc_is_ineligible_partner",
            "uc_non_dep_deductions",
            "uc_non_dep_deductions_renter_exempt",
        ]
    }


@PROPERTY_SETTINGS
@given(households=populations)
@example(households=[review_household(EVERY_BENEFIT)] * SLOTS)
@example(households=[review_household(dict(NO_BENEFITS, is_blind=True))] * SLOTS)
@example(
    households=[
        review_household(dict(NO_BENEFITS, armed_forces_independence_payment=5_000.0))
    ]
    * SLOTS
)
def test_an_excluded_partner_never_changes_the_deductions(simulation, households):
    without = calculate(simulation, households, partner_benefits=False)
    with_ = calculate(simulation, households, partner_benefits=True)
    # The generator flags every partner.
    assert with_["uc_is_ineligible_partner"][1::4].all()
    # Invariant 1.
    np.testing.assert_allclose(
        with_["uc_non_dep_deductions"], without["uc_non_dep_deductions"], atol=0.01
    )
    np.testing.assert_array_equal(
        with_["uc_non_dep_deductions_renter_exempt"],
        without["uc_non_dep_deductions_renter_exempt"],
    )


@PROPERTY_SETTINGS
@given(households=populations)
@example(households=[review_household(NO_BENEFITS)] * SLOTS)
def test_the_single_claimants_afip_removes_the_deductions(simulation, households):
    result = calculate(simulation, households, claimant_afip=True)
    families = slice(0, 2 * SLOTS, 2)
    # Invariant 2: para 15(1)(a) and (2)(c) with reg 2 head (f).
    assert result["uc_non_dep_deductions_renter_exempt"][families].all()
    np.testing.assert_array_equal(result["uc_non_dep_deductions"][families], 0)
