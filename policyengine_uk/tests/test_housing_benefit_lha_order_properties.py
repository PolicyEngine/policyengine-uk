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
2. Closed form: HB equals the formula above. This pins the formula to the
   law as read here; the hand-computed YAML cases, the bounds and the
   differential are the independent checks.
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
6. End to end: for pension-age renters, some with a working-age
   non-dependant, housing_benefit satisfies the closed form in the model's
   own applicable income, applicable amount and non-dependant deductions.

Each test also runs an explicit example where the two orders differ (one
unit for each term of the difference in invariant 5), so every test fails
under the old order whatever Hypothesis draws.
"""

import numpy as np
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

YEAR = 2026
# Engine values are float32; 0.05 covers rounding on amounts up to 100,000.
TOLERANCE = 0.05
PROPERTY_SETTINGS = settings(
    max_examples=15,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
RENTED_TENURES = ["RENT_FROM_COUNCIL", "RENT_FROM_HA", "RENT_PRIVATELY"]
NON_INCREASING = ["income", "non_dep_deductions"]
NON_DECREASING = ["rent", "lha_rate", "applicable_amount"]


def between(low, high):
    # Whole pence, so the arithmetic is exact to the penny.
    return st.integers(low * 100, high * 100).map(lambda pence: pence / 100)


def money(high):
    return between(0, high)


def above(floor, high):
    return st.integers(0, high * 100).map(
        lambda pence: (round(floor * 100) + pence) / 100
    )


@st.composite
def units(draw):
    # Hypothesis favours small draws. An LHA of a few pounds would leave
    # every tapered award at 0, where the two orders agree, so the LHA and
    # the applicable amount start at realistic levels.
    lha_rate = draw(between(2_000, 20_000))
    applicable_amount = draw(between(5_000, 25_000))
    return dict(
        tenure=draw(st.sampled_from(RENTED_TENURES)),
        lha_rate=lha_rate,
        # Many draws put the rent above the LHA and the income a little above
        # the applicable amount, where capping before or after the taper
        # differs.
        rent=draw(st.one_of(money(40_000), above(lha_rate, 20_000))),
        applicable_amount=applicable_amount,
        income=draw(
            st.one_of(st.just(0.0), money(60_000), above(applicable_amount, 10_000))
        ),
        non_dep_deductions=draw(st.one_of(st.just(0.0), money(5_000))),
    )


POPULATION = st.lists(units(), min_size=10, max_size=40)
BUMP = money(10_000).filter(lambda bump: bump > 0)

# One unit for each term of old - new = min(rent - LHA_cap, taper, old),
# worked by hand, and a council tenant for whom the orders agree. Taper is
# 0.65 * (income - applicable amount).
DIFFERENCE_EXAMPLES = [
    # The taper binds: taper 0.65 * 1,636.80 = 1,063.92; new 9,467.64 -
    # 1,063.92 = 8,403.72; old min(30,000 - 1,063.92, 9,467.64) = 9,467.64.
    dict(
        tenure="RENT_PRIVATELY",
        lha_rate=9_467.64,
        rent=30_000.0,
        applicable_amount=13_312.0,
        income=14_948.80,
        non_dep_deductions=0.0,
    ),
    # The rent excess binds: taper 0.65 * 8,000 = 5,200; new 9,467.64 -
    # 5,200 = 4,267.64; old min(12,000 - 5,200, 9,467.64) = 6,800; the
    # difference is 12,000 - 9,467.64 = 2,532.36.
    dict(
        tenure="RENT_PRIVATELY",
        lha_rate=9_467.64,
        rent=12_000.0,
        applicable_amount=13_312.0,
        income=21_312.0,
        non_dep_deductions=0.0,
    ),
    # The old award binds: taper 0.65 * 4,192.20 = 2,724.93; new max(0,
    # 8,000 - 6,000 - 2,724.93) = 0; old min(9,000 - 2,724.93, 8,000) -
    # 6,000 = 275.07.
    dict(
        tenure="RENT_PRIVATELY",
        lha_rate=8_000.0,
        rent=9_000.0,
        applicable_amount=7_807.80,
        income=12_000.0,
        non_dep_deductions=6_000.0,
    ),
    # rulespec-uk pipeline case 4: new 8,000 - 3,346.20 - 2,724.93 =
    # 1,928.87; old 6,275.07 - 3,346.20 = 2,928.87.
    dict(
        tenure="RENT_PRIVATELY",
        lha_rate=8_000.0,
        rent=9_000.0,
        applicable_amount=7_807.80,
        income=12_000.0,
        non_dep_deductions=3_346.20,
    ),
    # The same numbers for a council tenant: 2,928.87 under both orders.
    dict(
        tenure="RENT_FROM_COUNCIL",
        lha_rate=8_000.0,
        rent=9_000.0,
        applicable_amount=7_807.80,
        income=12_000.0,
        non_dep_deductions=3_346.20,
    ),
]


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
            "housing_benefit_LHA_rate": {YEAR: unit["lha_rate"]},
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
            "housing_benefit_LHA_rate",
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
@example(DIFFERENCE_EXAMPLES)
def test_bounds_closed_form_and_differential(population):
    values = calculate(population)
    hb = values["housing_benefit_entitlement"]
    rent = values["benunit_rent"]
    lha = values["lha"]
    tenures = np.array([unit["tenure"] for unit in population])
    # LHA tenants are exactly the private renters here.
    assert np.array_equal(lha, tenures == "RENT_PRIVATELY")
    assert np.allclose(
        values["LHA_cap"],
        np.minimum(rent, values["housing_benefit_LHA_rate"]),
        atol=TOLERANCE,
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


@settings(PROPERTY_SETTINGS, max_examples=10)
@given(POPULATION, st.lists(BUMP, min_size=5, max_size=5))
@example(DIFFERENCE_EXAMPLES, [1_000.0] * 5)
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
    at_or_above_lha = np.array(
        [
            unit["tenure"] == "RENT_PRIVATELY" and unit["rent"] >= unit["lha_rate"]
            for unit in population
        ]
    )
    after_rent = hb[1 + fields.index("rent")]
    assert np.allclose(
        after_rent[at_or_above_lha], before[at_or_above_lha], atol=TOLERANCE
    ), (population, bumps)


@st.composite
def pension_age_households(draw):
    lha_rate = draw(between(4_000, 15_000))
    return dict(
        ages=draw(st.lists(st.integers(67, 95), min_size=1, max_size=2)),
        # Often a little above the Pension Credit minimum guarantee, so the
        # taper bites without removing the award.
        state_pension=draw(st.one_of(above(14_000, 6_000), money(20_000))),
        private_pension=draw(st.one_of(st.just(0.0), money(5_000))),
        tenure=draw(st.sampled_from(RENTED_TENURES)),
        rent=draw(st.one_of(above(lha_rate, 15_000), money(30_000))),
        lha_rate=lha_rate,
        # A working-age adult in their own benefit unit, whose presence
        # brings a non-dependant deduction.
        non_dependant_earnings=draw(st.one_of(st.none(), money(40_000))),
    )


# The single pensioner from the issue (State Pension 16,000, above the
# minimum guarantee; rent 30,000 against an LHA of 9,467.64), alone and with
# a working-age non-dependant, and a pension-age couple in the same flat.
# Each has rent above the LHA and income above the applicable amount, where
# the two orders differ.
END_TO_END_EXAMPLE = [
    dict(
        ages=[70],
        state_pension=16_000.0,
        private_pension=0.0,
        tenure="RENT_PRIVATELY",
        rent=30_000.0,
        lha_rate=9_467.64,
        non_dependant_earnings=non_dependant_earnings,
    )
    for non_dependant_earnings in [None, 20_000.0]
] + [
    dict(
        ages=[70, 68],
        state_pension=12_000.0,
        private_pension=0.0,
        tenure="RENT_PRIVATELY",
        rent=30_000.0,
        lha_rate=9_467.64,
        non_dependant_earnings=None,
    )
]


def end_to_end(population):
    """Housing Benefit and its inputs, all computed by the model."""
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
            "housing_benefit_LHA_rate": {YEAR: unit["lha_rate"]},
        }
        household_members = list(names)
        if unit["non_dependant_earnings"] is not None:
            # Younger than the pensioners, so never the household head who
            # is liable for the rent.
            name = f"n{i}"
            people[name] = {
                "age": {YEAR: 30},
                "employment_income": {YEAR: unit["non_dependant_earnings"]},
            }
            benunits[f"n{i}"] = {"members": [name]}
            household_members.append(name)
        households[f"h{i}"] = {
            "members": household_members,
            "rent": {YEAR: unit["rent"]},
            "tenure_type": {YEAR: unit["tenure"]},
        }
    sim = Simulation(
        situation={"people": people, "benunits": benunits, "households": households}
    )
    values = {
        variable: np.asarray(sim.calculate(variable, YEAR), dtype=float)
        for variable in [
            "housing_benefit",
            "housing_benefit_eligible",
            "benunit_rent",
            "housing_benefit_LHA_rate",
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
    return values


@settings(PROPERTY_SETTINGS, max_examples=10)
@given(st.lists(pension_age_households(), min_size=5, max_size=20))
@example(END_TO_END_EXAMPLE)
def test_end_to_end_pension_age_housing_benefit(population):
    # The applicable income and amount and the non-dependant deductions are
    # the model's own, so this holds whatever the earnings disregard or the
    # Guarantee Credit passport do to them. Pensioners are exempt from the
    # benefit cap, and household calculations claim every entitled benefit.
    values = end_to_end(population)
    rent = values["benunit_rent"]
    lha = values["lha"]
    eligible_rent = np.where(lha, values["LHA_cap"], rent)
    expected = np.maximum(
        0,
        eligible_rent - values["housing_benefit_non_dep_deductions"] - values["taper"],
    )
    hb = values["housing_benefit"]
    eligible = values["housing_benefit_eligible"].astype(bool)
    assert np.allclose(hb[eligible], expected[eligible], atol=TOLERANCE), population
    assert np.all(hb[~eligible] == 0)
    lha_limit = np.minimum(rent, values["housing_benefit_LHA_rate"])
    assert np.all(hb[lha] <= lha_limit[lha] + TOLERANCE), population
