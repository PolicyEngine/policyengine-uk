"""Property-based tests for the Universal Credit minimum income floor.

UC Regs 2013 reg. 62 treats a claimant in gainful self-employment whose
earned income, after the deductions for their own income tax, NI and pension
contributions, is below their individual threshold as having that threshold.
The threshold is the reg. 90(2) amount "converted to net amounts by ...
deducting such amount for income tax and national insurance contributions as
the Secretary of State considers appropriate" (reg. 62(4)). For a member of a
couple the floor applies only while the couple's combined earned income is
below the couple threshold, and is reduced by any amount by which it and the
partner's earned income would exceed that threshold (reg. 62(3)).

Invariants, for any generated population of single people, couples,
mixed-age couples and couples with an adult child in their benefit unit, with
employment, self-employment profits and losses, pension contributions and
start-up periods, in England, Wales and Scotland:

1. The floor never lowers anyone's earned income, and changes it only for
   claimants it applies to.
2. The floor holds: a single claimant it applies to has at least the net
   floor. A member of a couple it applies to leaves the couple with at least
   the smaller of the couple threshold and their own threshold plus their
   partner's earned income, and is never lifted above their own threshold.
3. The couple threshold caps the top-up: whenever the floor lifts anyone,
   the couple's combined earned income is at most the couple threshold.
4. Differential against a reference: the model's reg. 62(2)-(3) conditions
   equal the closed form max(earned income, threshold - max(0, threshold +
   partner's earned income - couple threshold)), written here from the
   regulation.
5. Differential against the tax engine: the notional income tax deducted
   from the threshold equals the income tax the same person would pay with
   the gross threshold as their only income, as pay (no trading
   allowance). The notional NI equals the Class 2 and Class 4 they would
   pay on it as profits (the default basis) or, with the parameter
   switched, the primary Class 1 they would pay on it as pay. So the net
   floor never exceeds the gross threshold.
6. Monotone: more earnings never lower a benefit unit's earned income, and
   never raise UC before the benefit cap, with one intended exception: the
   model reads self-employment income of exactly zero as no
   self-employment, so a trading loss (which gets the floor, reg. 57(2) and
   ADM H4503) raised to exactly break-even loses it. Before this fix, a
   self-employed claimant under the floor was treated as having the gross
   threshold less the tax on their actual profits, so UC rose with their
   profits.

Marriage Allowance is switched off throughout: a transfer can lower one
partner's earned income when the other's earnings rise, which is a separate,
lawful, non-monotonicity.
"""

import numpy as np
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

PROPERTY_SETTINGS = settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
# 2020 has 12% Class 1 NI and the temporary UC uplift; 2026 current rates;
# 2027 the Finance Act 2026 rates.
YEARS = [2020, 2026, 2027]
TENURES = ["RENT_FROM_COUNCIL", "RENT_PRIVATELY", "OWNED_OUTRIGHT"]
REGIONS = ["LONDON", "NORTH_EAST", "WALES", "SCOTLAND"]
WORKING_AGE = st.integers(18, 64)
PENSION_AGE = st.integers(67, 80)
# The last shape has an adult child in the parents' benefit unit. The model
# flags at most two claimants (is_claimant_or_partner), here the parents; the
# couple is the two eldest claimants. The YAML tests flag a third by input.
SHAPES = {
    "single": [WORKING_AGE],
    "couple": [WORKING_AGE, WORKING_AGE],
    "mixed_age": [PENSION_AGE, WORKING_AGE],
    "couple_with_adult_child": [
        st.integers(40, 64),
        st.integers(40, 64),
        st.integers(18, 24),
    ],
}
# Profits and pay straddle the floor (about 16,000-23,000 gross).
# Profits and losses: a trading loss is nil self-employed earnings.
self_employment = st.one_of(st.just(0.0), st.floats(-10_000, 40_000))
employment = st.one_of(st.just(0.0), st.floats(0, 40_000))
pension = st.one_of(st.just(0.0), st.floats(0, 4_000))
bumps = st.floats(1, 10_000)
PERSON_VARIABLES = [
    "age",
    "is_uc_claimant",
    "uc_mif_applies",
    "uc_individual_earned_income_before_mif",
    "uc_individual_earned_income",
    "uc_minimum_income_floor",
    "uc_minimum_income_floor_gross",
    "uc_minimum_income_floor_income_tax",
    "uc_minimum_income_floor_national_insurance",
    "pays_scottish_income_tax",
]
BENUNIT_VARIABLES = ["uc_earned_income", "universal_credit_pre_benefit_cap"]


@st.composite
def families(draw):
    shape = draw(st.sampled_from(list(SHAPES)))
    adults = [
        dict(
            age=draw(age),
            self_employment_income=draw(self_employment),
            employment_income=draw(employment),
            pension_contributions=draw(pension),
            uc_is_in_startup_period=draw(st.booleans()),
        )
        for age in SHAPES[shape]
    ]
    return dict(
        adults=adults,
        children=[draw(st.integers(0, 15)) for _ in range(draw(st.integers(0, 2)))],
        tenure=draw(st.sampled_from(TENURES)),
        rent=draw(st.floats(0, 15_000)),
        region=draw(st.sampled_from(REGIONS)),
    )


populations = st.lists(families(), min_size=1, max_size=8)


def situation(units, year, bump=None):
    """One simulation holding every family.

    ``bump`` is (family index, adult index, variable, amount) to add.
    """
    people, benunits, households = {}, {}, {}
    for i, unit in enumerate(units):
        names = []
        for j, adult in enumerate(unit["adults"]):
            name = f"p{i}_{j}"
            person = {k: {year: v} for k, v in adult.items()}
            if bump is not None and bump[:2] == (i, j):
                variable, amount = bump[2], bump[3]
                person[variable] = {year: adult[variable] + amount}
            person["would_claim_marriage_allowance"] = {year: False}
            people[name] = person
            names.append(name)
        for k, age in enumerate(unit["children"]):
            name = f"c{i}_{k}"
            people[name] = {"age": {year: age}}
            names.append(name)
        benunits[f"b{i}"] = {"members": names}
        households[f"h{i}"] = {
            "members": names,
            "rent": {year: unit["rent"]},
            "tenure_type": {year: unit["tenure"]},
            "region": {year: unit["region"]},
        }
    return {"people": people, "benunits": benunits, "households": households}


def calculate(units, year, reform=None, **kwargs):
    sim = Simulation(situation=situation(units, year, **kwargs), reform=reform)
    values = {v: np.asarray(sim.calculate(v, year)) for v in PERSON_VARIABLES}
    for v in BENUNIT_VARIABLES:
        values[v] = np.asarray(sim.calculate(v, year))
        values[f"person_{v}"] = np.asarray(sim.calculate(v, year, map_to="person"))
    # The couple: at most the two eldest claimants of each benefit unit.
    flagged = values["is_uc_claimant"].astype(bool)
    unit = np.asarray(sim.populations["benunit"].members_entity_id)
    claimant = np.zeros(len(flagged), dtype=bool)
    for u in np.unique(unit):
        members = np.flatnonzero((unit == u) & flagged)
        eldest = members[np.argsort(-values["age"][members], kind="stable")][:2]
        claimant[eldest] = True
    values["in_couple"] = claimant
    values["floor_can_apply"] = values["uc_mif_applies"].astype(bool) & claimant
    before = values["uc_individual_earned_income_before_mif"]
    after = values["uc_individual_earned_income"]
    threshold = values["uc_minimum_income_floor"]
    # Benefit-unit sums over the claimants, mapped back to each person.
    values["claimant_before_sum"] = np.asarray(
        sim.map_result(
            sim.map_result(before * claimant, "person", "benunit"),
            "benunit",
            "person",
        )
    )
    values["claimant_after_sum"] = np.asarray(
        sim.map_result(
            sim.map_result(after * claimant, "person", "benunit"),
            "benunit",
            "person",
        )
    )
    values["couple_threshold"] = np.asarray(
        sim.map_result(
            sim.map_result(threshold * claimant, "person", "benunit"),
            "benunit",
            "person",
        )
    )
    values["lifted_in_unit"] = np.asarray(
        sim.map_result(
            sim.map_result(
                ((after > before + 0.01) & claimant).astype(float),
                "person",
                "benunit",
            ),
            "benunit",
            "person",
        )
    )
    values["claimants_in_unit"] = np.asarray(
        sim.map_result(
            sim.map_result(claimant.astype(float), "person", "benunit"),
            "benunit",
            "person",
        )
    )
    return values


@PROPERTY_SETTINGS
@given(units=populations, year=st.sampled_from(YEARS))
def test_floor_never_lowers_earned_income(units, year):
    v = calculate(units, year)
    before = v["uc_individual_earned_income_before_mif"]
    after = v["uc_individual_earned_income"]
    assert np.all(after >= before - 0.01), units
    unaffected = ~v["floor_can_apply"]
    np.testing.assert_allclose(
        after[unaffected], before[unaffected], atol=0.01, err_msg=str(units)
    )


@PROPERTY_SETTINGS
@given(units=populations, year=st.sampled_from(YEARS))
def test_floor_holds_for_singles_and_couples(units, year):
    v = calculate(units, year)
    applies = v["floor_can_apply"]
    before = v["uc_individual_earned_income_before_mif"]
    after = v["uc_individual_earned_income"]
    threshold = v["uc_minimum_income_floor"]
    single = v["claimants_in_unit"] == 1
    couple = v["claimants_in_unit"] == 2
    # Single claimants reach the net floor.
    assert np.all(after[applies & single] >= threshold[applies & single] - 0.01), units
    # Couples reach the smaller of the couple threshold and the person's own
    # threshold plus their partner's earned income.
    partner = v["claimant_before_sum"] - before
    target = np.minimum(v["couple_threshold"], threshold + partner)
    combined = after + partner
    m = applies & couple
    assert np.all(combined[m] >= target[m] - 0.01), units
    # Nobody is lifted above their own threshold.
    assert np.all(after <= np.maximum(before, threshold) + 0.01), units


@PROPERTY_SETTINGS
@given(units=populations, year=st.sampled_from(YEARS))
def test_top_up_never_takes_couple_above_couple_threshold(units, year):
    v = calculate(units, year)
    lifted_unit = v["lifted_in_unit"] > 0
    assert np.all(
        v["claimant_after_sum"][lifted_unit]
        <= v["couple_threshold"][lifted_unit] + 0.01
    ), units


@PROPERTY_SETTINGS
@given(units=populations, year=st.sampled_from(YEARS))
def test_matches_closed_form_of_regulation_62(units, year):
    v = calculate(units, year)
    before = v["uc_individual_earned_income_before_mif"]
    threshold = v["uc_minimum_income_floor"]
    claimant = v["in_couple"]
    partner = v["claimant_before_sum"] - before * claimant
    floor = threshold - np.maximum(0, threshold + partner - v["couple_threshold"])
    expected = np.where(v["floor_can_apply"], np.maximum(before, floor), before)
    np.testing.assert_allclose(
        v["uc_individual_earned_income"], expected, atol=0.01, err_msg=str(units)
    )


SELF_EMPLOYED_NI = (
    "gov.dwp.universal_credit.means_test.minimum_income_floor."
    "self_employed_national_insurance"
)


@PROPERTY_SETTINGS
@given(
    units=populations,
    year=st.sampled_from(YEARS),
    self_employed=st.booleans(),
)
def test_notional_deductions_equal_tax_on_threshold_as_only_income(
    units, year, self_employed
):
    reform = {SELF_EMPLOYED_NI: {"2013-01-01.2100-12-31": self_employed}}
    v = calculate(units, year, reform=reform)
    adults = v["age"] >= 16
    gross = v["uc_minimum_income_floor_gross"][adults]
    scottish = v["pays_scottish_income_tax"][adults].astype(bool)
    ages = v["age"][adults]
    # Each adult alone twice: paid their gross threshold from employment, and
    # with profits of that amount.
    people, benunits, households = {}, {}, {}
    for k, (amount, age, in_scotland) in enumerate(zip(gross, ages, scottish)):
        for kind, income in [
            ("e", "employment_income"),
            ("s", "self_employment_income"),
        ]:
            name = f"{kind}{k}"
            people[name] = {
                "age": {year: int(age)},
                income: {year: float(amount)},
                "would_claim_marriage_allowance": {year: False},
            }
            benunits[f"b{name}"] = {"members": [name]}
            households[f"h{name}"] = {
                "members": [name],
                "region": {year: "SCOTLAND" if in_scotland else "NORTH_EAST"},
            }
    alone = Simulation(
        situation={"people": people, "benunits": benunits, "households": households}
    )
    employee = np.arange(len(people)) % 2 == 0
    np.testing.assert_allclose(
        v["uc_minimum_income_floor_income_tax"][adults],
        np.asarray(alone.calculate("income_tax", year))[employee],
        atol=0.01,
        err_msg=str(units),
    )
    if self_employed:
        expected_ni = (
            np.asarray(alone.calculate("ni_class_2", year))
            + np.asarray(alone.calculate("ni_class_4", year))
        )[~employee]
    else:
        expected_ni = np.asarray(alone.calculate("ni_class_1_employee", year))[employee]
    np.testing.assert_allclose(
        v["uc_minimum_income_floor_national_insurance"][adults],
        expected_ni,
        atol=0.01,
        err_msg=str(units),
    )
    net = v["uc_minimum_income_floor"]
    assert np.all(net <= v["uc_minimum_income_floor_gross"] + 0.01)
    assert np.all(net >= 0)


@st.composite
def bumped(draw):
    units = draw(populations)
    i = draw(st.integers(0, len(units) - 1))
    j = draw(st.integers(0, len(units[i]["adults"]) - 1))
    variable = draw(st.sampled_from(["self_employment_income", "employment_income"]))
    amount = draw(bumps)
    # The intended exception to monotonicity: a loss raised to exactly zero.
    assume(units[i]["adults"][j][variable] + amount != 0)
    return units, (i, j, variable, amount)


@PROPERTY_SETTINGS
@given(case=bumped(), year=st.sampled_from(YEARS))
def test_more_earnings_never_lower_earned_income_or_raise_uc(case, year):
    units, bump = case
    low = calculate(units, year)
    high = calculate(units, year, bump=bump)
    assert np.all(high["uc_earned_income"] >= low["uc_earned_income"] - 0.01), (
        bump,
        units,
    )
    assert np.all(
        high["universal_credit_pre_benefit_cap"]
        <= low["universal_credit_pre_benefit_cap"] + 0.01
    ), (bump, units)
