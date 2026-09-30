"""Property-based tests for the order of the LHA cap and the taper.

Where a maximum rent (LHA) applies, it is the eligible rent (SI 2006/213 and
SI 2006/214 reg 12D(2)(a)), and it is the rent where the rent is below the
LHA (reg 13D(5)). The appropriate maximum Housing Benefit is the eligible rent
less non-dependant deductions (reg 70; SPC reg 50), and 65% of the excess of
income over the applicable amount is deducted from it (SSCBA 1992
s.130(3)(b); reg 71; SPC reg 51). So, with taper = 0.65 * max(0, income -
applicable amount):

    HB = max(0, eligible rent - non-dependant deductions - taper)

where the eligible rent is min(rent, LHA) for LHA tenants and the rent for
social tenants.

Invariants, for any generated population of benefit units:

1. Bounds: 0 <= HB <= eligible rent <= rent, and for LHA tenants
   HB <= LHA_cap = min(rent, LHA rate).
2. Closed form: HB equals the formula above.
3. Monotonicity: HB is non-increasing in applicable income and in
   non-dependant deductions, and non-decreasing in rent, the LHA rate and the
   applicable amount.
4. Rent above the LHA: for an LHA tenant whose rent is at or above the LHA
   rate, raising the rent further leaves HB unchanged.
5. Differential against the formula before this change, which capped after
   the taper (max(0, min(max(0, rent - taper), LHA_cap) - deductions)):
   the two agree for social tenants, where the rent is at or below the LHA,
   where there is no taper, and where the old award was 0. Otherwise the new
   award is lower, and old - new = min(rent - LHA_cap, taper, old) exactly.
   This difference is intended.
6. End to end: for pension-age renters, housing_benefit satisfies the closed
   form in the model's own applicable income and amount.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

YEAR = 2026
# Engine values are float32; 0.05 covers rounding on amounts up to 100,000.
TOLERANCE = 0.05
PROPERTY_SETTINGS = settings(
    max_examples=25,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
RENTED_TENURES = ["RENT_FROM_COUNCIL", "RENT_FROM_HA", "RENT_PRIVATELY"]
NON_INCREASING = ["income", "non_dep_deductions"]
NON_DECREASING = ["rent", "lha_rate", "applicable_amount"]


def money(high):
    # Whole pence, so the arithmetic is exact to the penny.
    return st.integers(0, high * 100).map(lambda pence: pence / 100)


def above(floor, high):
    return st.integers(0, high * 100).map(
        lambda pence: (round(floor * 100) + pence) / 100
    )


@st.composite
def units(draw):
    lha_rate = draw(money(30_000))
    applicable_amount = draw(money(25_000))
    return dict(
        tenure=draw(st.sampled_from(RENTED_TENURES)),
        lha_rate=lha_rate,
        # Many draws put the rent above the LHA and the income above the
        # applicable amount, where capping before or after the taper differs.
        rent=draw(st.one_of(money(40_000), above(lha_rate, 20_000))),
        applicable_amount=applicable_amount,
        income=draw(
            st.one_of(st.just(0.0), money(60_000), above(applicable_amount, 15_000))
        ),
        non_dep_deductions=draw(st.one_of(st.just(0.0), money(10_000))),
    )


POPULATION = st.lists(units(), min_size=1, max_size=40)
BUMP = money(10_000).filter(lambda bump: bump > 0)


def calculate(population):
    """Housing Benefit inputs and entitlement for independent benefit units.

    Each unit is a one-person benefit unit in its own household, so one
    simulation can hold a population and its perturbed copies.
    """
    people, benunits, households = {}, {}, {}
    for i, unit in enumerate(population):
        name = f"p{i}"
        people[name] = {"age": {YEAR: 70}}
        benunits[f"b{i}"] = {
            "members": [name],
            "BRMA_LHA_rate": {YEAR: unit["lha_rate"]},
            "housing_benefit_applicable_amount": {YEAR: unit["applicable_amount"]},
            "housing_benefit_applicable_income": {YEAR: unit["income"]},
            "housing_benefit_non_dep_deductions": {YEAR: unit["non_dep_deductions"]},
        }
        households[f"h{i}"] = {
            "members": [name],
            "rent": {YEAR: unit["rent"]},
            "tenure_type": {YEAR: unit["tenure"]},
        }
    sim = Simulation(
        situation={"people": people, "benunits": benunits, "households": households}
    )
    values = {
        variable: np.asarray(sim.calculate(variable, YEAR), dtype=float)
        for variable in [
            "housing_benefit_entitlement",
            "benunit_rent",
            "BRMA_LHA_rate",
            "LHA_cap",
            "LHA_eligible",
            "housing_benefit_applicable_amount",
            "housing_benefit_applicable_income",
            "housing_benefit_non_dep_deductions",
        ]
    }
    rate = sim.tax_benefit_system.parameters(
        YEAR
    ).gov.dwp.housing_benefit.means_test.withdrawal_rate
    values["lha"] = values["LHA_eligible"].astype(bool)
    values["taper"] = rate * np.maximum(
        0,
        values["housing_benefit_applicable_income"]
        - values["housing_benefit_applicable_amount"],
    )
    values["eligible_rent"] = np.where(
        values["lha"], values["LHA_cap"], values["benunit_rent"]
    )
    return values


def old_entitlement(values):
    """housing_benefit_entitlement as computed before this change."""
    final_amount = np.maximum(0, values["benunit_rent"] - values["taper"])
    capped = np.minimum(final_amount, values["LHA_cap"])
    amount = np.where(values["lha"], capped, final_amount)
    return np.maximum(0, amount - values["housing_benefit_non_dep_deductions"])


@PROPERTY_SETTINGS
@given(POPULATION)
def test_bounds_closed_form_and_differential(population):
    values = calculate(population)
    hb = values["housing_benefit_entitlement"]
    rent = values["benunit_rent"]
    lha = values["lha"]
    tenures = np.array([unit["tenure"] for unit in population])
    # LHA tenants are exactly the private renters here.
    assert np.array_equal(lha, tenures == "RENT_PRIVATELY")
    assert np.allclose(
        values["LHA_cap"], np.minimum(rent, values["BRMA_LHA_rate"]), atol=TOLERANCE
    )

    # 1. Bounds.
    assert np.all(hb >= 0)
    assert np.all(hb <= values["eligible_rent"] + TOLERANCE)
    assert np.all(values["eligible_rent"] <= rent + TOLERANCE)
    assert np.all(hb[lha] <= values["LHA_cap"][lha] + TOLERANCE)

    # 2. Closed form.
    expected = np.maximum(
        0,
        values["eligible_rent"]
        - values["housing_benefit_non_dep_deductions"]
        - values["taper"],
    )
    assert np.allclose(hb, expected, atol=TOLERANCE), population

    # 5. Differential against capping after the taper.
    old = old_entitlement(values)
    rent_excess = rent - values["LHA_cap"]
    agree = ~lha | (rent_excess <= 0) | (values["taper"] == 0) | (old == 0)
    assert np.allclose(hb[agree], old[agree], atol=TOLERANCE), population
    assert np.all(hb <= old + TOLERANCE)
    # Intended difference: the taper now comes off the LHA, not the rent.
    difference = np.where(
        lha, np.minimum(np.minimum(rent_excess, values["taper"]), old), 0
    )
    assert np.allclose(old - hb, difference, atol=TOLERANCE), population


@settings(PROPERTY_SETTINGS, max_examples=15)
@given(POPULATION, st.lists(BUMP, min_size=5, max_size=5))
def test_monotonicity(population, bumps):
    fields = NON_INCREASING + NON_DECREASING
    variants = [population] + [
        [{**unit, field: unit[field] + bump} for unit in population]
        for field, bump in zip(fields, bumps)
    ]
    hb = calculate([unit for variant in variants for unit in variant])[
        "housing_benefit_entitlement"
    ].reshape(len(variants), len(population))
    before = hb[0]
    for after, field in zip(hb[1:], fields):
        if field in NON_INCREASING:
            assert np.all(after <= before + TOLERANCE), (population, field, bumps)
        else:
            assert np.all(after >= before - TOLERANCE), (population, field, bumps)

    # 4. For LHA tenants already at or above the LHA, more rent changes
    # nothing: the eligible rent is the LHA.
    above = np.array(
        [
            unit["tenure"] == "RENT_PRIVATELY" and unit["rent"] >= unit["lha_rate"]
            for unit in population
        ]
    )
    after_rent = hb[1 + fields.index("rent")]
    assert np.allclose(after_rent[above], before[above], atol=TOLERANCE), (
        population,
        bumps,
    )


@st.composite
def pension_age_households(draw):
    lha_rate = draw(money(20_000))
    return dict(
        ages=draw(st.lists(st.integers(67, 95), min_size=1, max_size=2)),
        # Often above the Pension Credit minimum guarantee, so the taper bites.
        state_pension=draw(st.one_of(above(14_000, 10_000), money(20_000))),
        private_pension=draw(st.one_of(st.just(0.0), money(30_000))),
        tenure=draw(st.sampled_from(RENTED_TENURES)),
        rent=draw(st.one_of(above(lha_rate, 15_000), money(30_000))),
        lha_rate=lha_rate,
    )


@settings(PROPERTY_SETTINGS, max_examples=15)
@given(st.lists(pension_age_households(), min_size=1, max_size=20))
def test_end_to_end_pension_age_housing_benefit(population):
    # The applicable income and amount are the model's own, so this holds
    # whatever the earnings disregard or the Guarantee Credit passport do to
    # them. Pensioners are exempt from the benefit cap, and household
    # calculations claim every entitled benefit.
    people, benunits, households = {}, {}, {}
    for i, unit in enumerate(population):
        names = []
        for j, age in enumerate(unit["ages"]):
            name = f"p{i}_{j}"
            people[name] = {
                "age": {YEAR: age},
                "state_pension_reported": {YEAR: unit["state_pension"]},
                "private_pension_income": {YEAR: unit["private_pension"]},
            }
            names.append(name)
        benunits[f"b{i}"] = {
            "members": names,
            "BRMA_LHA_rate": {YEAR: unit["lha_rate"]},
        }
        households[f"h{i}"] = {
            "members": names,
            "rent": {YEAR: unit["rent"]},
            "tenure_type": {YEAR: unit["tenure"]},
        }
    sim = Simulation(
        situation={"people": people, "benunits": benunits, "households": households}
    )

    def get(variable):
        return np.asarray(sim.calculate(variable, YEAR), dtype=float)

    rate = sim.tax_benefit_system.parameters(
        YEAR
    ).gov.dwp.housing_benefit.means_test.withdrawal_rate
    rent = get("benunit_rent")
    lha = get("LHA_eligible").astype(bool)
    eligible_rent = np.where(lha, get("LHA_cap"), rent)
    taper = rate * np.maximum(
        0,
        get("housing_benefit_applicable_income")
        - get("housing_benefit_applicable_amount"),
    )
    expected = np.maximum(
        0, eligible_rent - get("housing_benefit_non_dep_deductions") - taper
    )
    hb = get("housing_benefit")
    eligible = get("housing_benefit_eligible").astype(bool)
    assert np.allclose(hb[eligible], expected[eligible], atol=TOLERANCE), population
    assert np.all(hb[~eligible] == 0)
    lha_limit = np.minimum(rent, get("BRMA_LHA_rate"))
    assert np.all(hb[lha] <= lha_limit[lha] + TOLERANCE), population
