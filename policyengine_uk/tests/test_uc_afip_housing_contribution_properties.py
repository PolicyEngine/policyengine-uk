"""Property-based tests: armed forces independence payment (AFIP) counts as
attendance allowance in the Universal Credit housing cost contribution rules.

Under UC Regs 2013 Sch 4 para 13, DWP deducts a housing cost contribution for
each non-dependant in the renter's extended benefit unit. Under para 16(2)(d)
it deducts none for a non-dependant "in receipt of attendance allowance", and
the Secretary of State defines that term in reg 2 to include AFIP (head (f)).
The Secretary of State names no AFIP head among the descriptions of unearned
income in reg 66, and the model leaves AFIP out of the renter's unearned
income.

Each generated household has a renter, who claims Universal Credit, and a
non-dependant in a family of their own that does not claim. The tests
calculate the same households with no AFIP, then with a positive AFIP for the
non-dependant, the renter or both. Invariants:

1. Raising AFIP from nil to any positive amount never lowers Universal
   Credit and never raises the housing cost contributions.
2. The model exempts a non-dependant who receives AFIP and charges no
   contribution for them.
3. Where only the non-dependant receives AFIP, the renter's housing costs
   element rises by no more than the contributions fall (under para 14(3),
   DWP reduces the element to nil and no further), and Universal Credit rises
   by no more than the element.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

YEAR = 2026
# Fixed slots, so one simulation serves every example. Each slot's tenure and
# region are fixed; the generated inputs change from example to example.
TENURES = ["RENT_FROM_COUNCIL", "RENT_FROM_HA", "RENT_PRIVATELY"]
REGIONS = ["NORTH_WEST", "LONDON", "SCOTLAND", "WALES"]
SLOTS = 12
PROPERTY_SETTINGS = settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)


def situation():
    people, benunits, households = {}, {}, {}
    for i in range(SLOTS):
        renter, non_dependant = f"renter_{i}", f"non_dependant_{i}"
        for name, head in [(renter, True), (non_dependant, False)]:
            people[name] = {
                "age": {YEAR: 40},
                "is_household_head": {YEAR: head},
                "is_claimant_or_partner": {YEAR: True},
                "employment_income": {YEAR: 0},
                "pip_dl": {YEAR: 0},
                "armed_forces_independence_payment": {YEAR: 0},
            }
        benunits[f"renter_family_{i}"] = {
            "members": [renter],
            "would_claim_uc": {YEAR: True},
            "claims_all_entitled_benefits": {YEAR: False},
        }
        benunits[f"non_dependant_family_{i}"] = {
            "members": [non_dependant],
            "would_claim_uc": {YEAR: False},
            "claims_all_entitled_benefits": {YEAR: False},
        }
        households[f"household_{i}"] = {
            "members": [renter, non_dependant],
            "rent": {YEAR: 6_000},
            "tenure_type": {YEAR: TENURES[i % len(TENURES)]},
            "region": {YEAR: REGIONS[i % len(REGIONS)]},
        }
    return {"people": people, "benunits": benunits, "households": households}


@pytest.fixture(scope="module")
def simulation(cloned_uk_tax_benefit_system):
    return Simulation(situation=situation())


money = st.floats(0, 60_000, allow_nan=False)
# The model holds amounts as 32-bit floats, which store an amount below about
# 1e-45 as zero, so positive amounts start at a penny.
positive_afip = st.floats(0.01, 50_000, allow_nan=False)


@st.composite
def household(draw):
    afip_to_non_dependant = draw(st.booleans())
    return dict(
        renter_age=draw(st.integers(18, 64)),
        renter_earnings=draw(st.one_of(st.just(0.0), money)),
        rent=draw(st.one_of(st.floats(0, 2_000), st.floats(2_000, 20_000))),
        non_dependant_age=draw(st.integers(18, 85)),
        non_dependant_earnings=draw(st.one_of(st.just(0.0), money)),
        non_dependant_pip=draw(
            st.one_of(st.just(0.0), st.just(0.0), st.floats(1_000, 6_000))
        ),
        afip_to_non_dependant=afip_to_non_dependant,
        # At least one person receives AFIP in each household.
        afip_to_renter=draw(st.booleans()) or not afip_to_non_dependant,
        afip=draw(positive_afip),
    )


populations = st.lists(household(), min_size=SLOTS, max_size=SLOTS)


def issue_example():
    """The issue's household (PolicyEngine/policyengine-uk#2802): a renter
    aged 40 with no earnings paying the council 6,000 a year, and a
    non-dependant aged 25 earning 20,000 who receives AFIP."""
    return [
        dict(
            renter_age=40,
            renter_earnings=0.0,
            rent=6_000.0,
            non_dependant_age=25,
            non_dependant_earnings=20_000.0,
            non_dependant_pip=0.0,
            afip_to_non_dependant=True,
            afip_to_renter=False,
            afip=9_000.0,
        )
    ] * SLOTS


def person_array(households, renter_key, non_dependant_key):
    values = []
    for h in households:
        values += [h[renter_key], h[non_dependant_key]]
    return np.array(values, dtype=float)


def calculate(sim, households, afip):
    sim.set_input(
        "age", YEAR, person_array(households, "renter_age", "non_dependant_age")
    )
    sim.set_input(
        "employment_income",
        YEAR,
        person_array(households, "renter_earnings", "non_dependant_earnings"),
    )
    pip = []
    for h in households:
        pip += [0.0, h["non_dependant_pip"]]
    sim.set_input("pip_dl", YEAR, np.array(pip))
    sim.set_input("armed_forces_independence_payment", YEAR, afip)
    sim.set_input("rent", YEAR, np.array([h["rent"] for h in households]))
    sim.drop_computed_arrays()
    return {
        name: np.asarray(sim.calculate(name, YEAR))
        for name in [
            "universal_credit",
            "uc_non_dep_deductions",
            "uc_housing_costs_element",
            "uc_individual_non_dep_deduction",
            "uc_non_dep_deduction_exempt",
        ]
    }


def afip_amounts(households):
    afip = []
    for h in households:
        afip += [
            h["afip"] if h["afip_to_renter"] else 0.0,
            h["afip"] if h["afip_to_non_dependant"] else 0.0,
        ]
    return np.array(afip)


@PROPERTY_SETTINGS
@given(households=populations)
@example(households=issue_example())
def test_afip_never_lowers_uc_and_exempts_the_non_dependant(simulation, households):
    before = calculate(simulation, households, np.zeros(2 * SLOTS))
    after = calculate(simulation, households, afip_amounts(households))
    renter_family = slice(0, 2 * SLOTS, 2)
    non_dependant = slice(1, 2 * SLOTS, 2)

    # Invariant 1.
    uc_change = (after["universal_credit"] - before["universal_credit"])[renter_family]
    contribution_change = (
        after["uc_non_dep_deductions"] - before["uc_non_dep_deductions"]
    )[renter_family]
    assert (uc_change >= -0.01).all(), uc_change
    assert (contribution_change <= 0.01).all(), contribution_change

    # Invariant 2: Sch 4 para 16(2)(d) with reg 2 head (f).
    receives = np.array([h["afip_to_non_dependant"] for h in households])
    assert after["uc_non_dep_deduction_exempt"][non_dependant][receives].all()
    np.testing.assert_array_equal(
        after["uc_individual_non_dep_deduction"][non_dependant][receives], 0
    )

    # Invariant 3.
    only_non_dependant = receives & ~np.array([h["afip_to_renter"] for h in households])
    element_change = (
        after["uc_housing_costs_element"] - before["uc_housing_costs_element"]
    )[renter_family]
    assert (element_change[only_non_dependant] >= -0.01).all()
    assert (
        element_change[only_non_dependant]
        <= -contribution_change[only_non_dependant] + 0.01
    ).all()
    assert (
        uc_change[only_non_dependant] <= element_change[only_non_dependant] + 0.01
    ).all()


# Under Sch 4 para 29(5), DWP excepts from the shared accommodation rate a
# renter under 35 who receives the DLA care component at the middle or highest
# rate, attendance allowance or the PIP daily living component. The exception
# list names uc_receives_attendance_allowance, which applies the reg 2
# definition. The differential below checks that the list gives the same result
# as one naming attendance allowance and AFIP directly.
LHA_EXCEPTIONS = "gov.dwp.LHA.shared_accommodation_exception_benefits"
PREVIOUS_LHA_EXCEPTIONS = [
    "attendance_allowance",
    "dla_sc_middle_plus",
    "pip_dl",
    "armed_forces_independence_payment",
]
RENTER_OUTPUTS = [
    "is_lha_shared_accommodation_rate_specified_renter",
    "universal_credit",
]


def single_renters():
    people, benunits, households = {}, {}, {}
    for i in range(SLOTS):
        renter = f"renter_{i}"
        people[renter] = {
            "age": {YEAR: 30},
            "is_household_head": {YEAR: True},
            "is_claimant_or_partner": {YEAR: True},
            "employment_income": {YEAR: 0},
            "attendance_allowance": {YEAR: 0},
            "dla_sc_middle_plus": {YEAR: False},
            "pip_dl": {YEAR: 0},
            "armed_forces_independence_payment": {YEAR: 0},
        }
        benunits[f"renter_family_{i}"] = {
            "members": [renter],
            "would_claim_uc": {YEAR: True},
            "claims_all_entitled_benefits": {YEAR: False},
        }
        households[f"household_{i}"] = {
            "members": [renter],
            "rent": {YEAR: 9_000},
            "tenure_type": {YEAR: "RENT_PRIVATELY"},
            "region": {YEAR: REGIONS[i % len(REGIONS)]},
        }
    return {"people": people, "benunits": benunits, "households": households}


@pytest.fixture(scope="module")
def renter_simulation(cloned_uk_tax_benefit_system):
    return Simulation(situation=single_renters())


sometimes = st.one_of(st.just(0.0), st.just(0.0), st.floats(1, 9_000))


@st.composite
def renter(draw):
    return dict(
        age=draw(st.integers(18, 40)),
        attendance_allowance=draw(sometimes),
        dla_sc_middle_plus=draw(st.booleans()),
        pip_dl=draw(sometimes),
        armed_forces_independence_payment=draw(sometimes),
    )


def renter_outputs(sim):
    sim.drop_computed_arrays()
    return {name: np.asarray(sim.calculate(name, YEAR)) for name in RENTER_OUTPUTS}


@PROPERTY_SETTINGS
@given(renters=st.lists(renter(), min_size=SLOTS, max_size=SLOTS))
@example(
    renters=[
        dict(
            age=age,
            attendance_allowance=0.0,
            dla_sc_middle_plus=False,
            pip_dl=0.0,
            armed_forces_independence_payment=afip,
        )
        for age in (25, 34, 35, 40)
        for afip in (0.0, 9_000.0, 0.01)
    ]
)
def test_shared_accommodation_exceptions_match_the_previous_list(
    renter_simulation, renters
):
    sim = renter_simulation
    for name in renters[0]:
        sim.set_input(name, YEAR, np.array([r[name] for r in renters]))
    current = renter_outputs(sim)
    parameter = sim.tax_benefit_system.parameters.get_child(LHA_EXCEPTIONS)
    listed = parameter(f"{YEAR}-01-01")
    try:
        parameter.update(period=str(YEAR), value=PREVIOUS_LHA_EXCEPTIONS)
        sim.tax_benefit_system.reset_parameter_caches()
        previous = renter_outputs(sim)
    finally:
        parameter.update(period=str(YEAR), value=listed)
        sim.tax_benefit_system.reset_parameter_caches()
        sim.drop_computed_arrays()
    for name in RENTER_OUTPUTS:
        np.testing.assert_array_equal(current[name], previous[name], err_msg=name)
