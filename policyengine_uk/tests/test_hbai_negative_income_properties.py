"""HBAI resets a negative household income to zero before housing costs.

"Negative incomes BHC are reset to zero, but negative AHC incomes calculated
from the adjusted BHC incomes are possible. Where incomes have been adjusted
to zero BHC, income AHC is derived from the adjusted BHC income." (HBAI
Background Information and Methodology report FYE 2025, "Negative incomes".)

Properties, for any population of households (b is
hbai_household_net_income_before_reset_to_zero, HC the HBAI housing costs:
rent, water and sewerage charges, mortgage interest, structural insurance,
and ground rent and service charges):

1. Reset: hbai_household_net_income = max(0, b), so it and its equivalised
   and real versions are never negative.
2. Differential: b equals the HBAI components summed outside the model
   (HBAI_HOUSEHOLD_NET_INCOME_ADDS less HBAI_HOUSEHOLD_NET_INCOME_SUBTRACTS).
3. After housing costs: hbai_household_net_income_ahc = max(0, b) - HC, which
   is negative whenever HC exceeds the reset income.
4. Headcounts: every poverty flag (absolute, deep, relative; BHC and AHC)
   equals the flag computed from the income before the reset. Zero is below
   any absolute line, and the reset moves no one across the median as long as
   fewer than half of people have an income of zero or less before the reset.
   Otherwise the BHC median is itself reset to zero, and no one is in relative
   poverty before housing costs.
5. Gaps: each gap is measured from the reset income, so the BHC gaps never
   exceed their line, and every gap is at most the gap before the reset, with
   equality when b >= 0.
6. Means: the weighted total of the reset income exceeds that of b by exactly
   the weighted sum of the negative parts of b.
7. Deciles: every household has a decile from 1 to 10 (none is left out), and
   deciles never fall as equivalised income rises. Households at zero share
   one decile, the lowest; it is decile 1 when they hold less than a tenth of
   people (equal incomes take the rank at the top of their group).
8. Labour supply responses measure b, the actual budget constraint: a pay rise
   for a household below zero raises b, while the reset income stays at zero.

Comparisons allow float32 rounding: the model stores values as float32.
"""

import inspect

import numpy as np
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st
from microdf import MicroSeries

from policyengine_uk import Simulation
from policyengine_uk.dynamics import labour_supply, progression
from policyengine_uk.variables.household.income.hbai_household_net_income import (
    HBAI_HOUSEHOLD_NET_INCOME_ADDS,
    HBAI_HOUSEHOLD_NET_INCOME_SUBTRACTS,
)

BEFORE_RESET = "hbai_household_net_income_before_reset_to_zero"
HOUSING_COSTS = [
    "rent",
    "water_and_sewerage_charges",
    "mortgage_interest_repayment",
    "structural_insurance_payments",
    "housing_service_charges",
]
YEARS = [2024, 2025, 2026]
PROPERTY_SETTINGS = settings(
    max_examples=12,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)


def money(*values):
    return st.sampled_from(values)


@st.composite
def households(draw):
    renter = draw(st.booleans())
    return {
        "adults": [
            {
                "age": draw(st.sampled_from([25, 40, 55, 70])),
                "employment_income": draw(money(0, 0, 6_000, 20_000, 60_000)),
                # Maintenance paid and pension contributions are deducted in
                # HBAI and can exceed income, which makes b negative.
                "maintenance_expenses": draw(money(0, 0, 4_000, 15_000, 40_000)),
                "personal_pension_contributions": draw(money(0, 0, 5_000)),
            }
            for _ in range(draw(st.integers(1, 2)))
        ],
        "children": draw(st.integers(0, 2)),
        "would_claim_uc": draw(st.booleans()),
        "household": {
            "council_tax": draw(money(0, 1_200, 2_500)),
            "housing_service_charges": draw(money(300, 600, 1_200)),
            "tenure_type": "RENT_PRIVATELY" if renter else "OWNED_WITH_MORTGAGE",
            "rent": draw(money(4_000, 9_000, 15_000)) if renter else 0,
            "mortgage_interest_repayment": 0 if renter else draw(money(0, 3_000)),
            "water_and_sewerage_charges": draw(money(0, 450)),
            "structural_insurance_payments": 0 if renter else draw(money(0, 250)),
        },
    }


@st.composite
def populations(draw):
    return {
        "year": draw(st.sampled_from(YEARS)),
        "households": draw(st.lists(households(), min_size=2, max_size=8)),
    }


def adult(age, earnings, maintenance=0, pension=0):
    return {
        "age": age,
        "employment_income": earnings,
        "maintenance_expenses": maintenance,
        "personal_pension_contributions": pension,
    }


def home(council_tax, rent=0, mortgage=0, water=0, insurance=0, charges=600):
    return {
        "council_tax": council_tax,
        "tenure_type": "RENT_PRIVATELY" if rent else "OWNED_WITH_MORTGAGE",
        "rent": rent,
        "mortgage_interest_repayment": mortgage,
        "water_and_sewerage_charges": water,
        "structural_insurance_payments": insurance,
        "housing_service_charges": charges,
    }


# A population the properties always check, whatever Hypothesis draws: two
# households whose deductions exceed their income (one renting, one buying),
# and four with positive incomes, so most people are above zero and the
# relative-poverty properties apply.
PINNED = {
    "year": 2024,
    "households": [
        {
            "adults": [adult(40, 6_000, maintenance=15_000)],
            "children": 0,
            "would_claim_uc": False,
            "household": home(1_200, rent=9_000, water=450),
        },
        {
            "adults": [adult(55, 0, maintenance=4_000, pension=5_000)],
            "children": 1,
            "would_claim_uc": False,
            "household": home(2_500, mortgage=3_000, insurance=250),
        },
        {
            "adults": [adult(40, 20_000), adult(40, 60_000)],
            "children": 2,
            "would_claim_uc": True,
            "household": home(2_500, mortgage=3_000),
        },
        {
            "adults": [adult(25, 20_000)],
            "children": 0,
            "would_claim_uc": True,
            "household": home(1_200, rent=9_000),
        },
        {
            "adults": [adult(70, 0)],
            "children": 0,
            "would_claim_uc": True,
            "household": home(1_200, rent=4_000),
        },
        {
            "adults": [adult(55, 60_000)],
            "children": 0,
            "would_claim_uc": True,
            "household": home(2_500),
        },
    ],
}


# One household whose maintenance payments exceed its income among ten single
# earners: the household at zero holds 1 of 11 people, under a tenth, so it is
# in decile 1.
PINNED_FEW_AT_ZERO = {
    "year": 2025,
    "households": [
        {
            "adults": [adult(40, 0, maintenance=15_000)],
            "children": 0,
            "would_claim_uc": False,
            "household": home(1_200, rent=6_000),
        }
    ]
    + [
        {
            "adults": [adult(30, earnings)],
            "children": 0,
            "would_claim_uc": True,
            "household": home(1_200, rent=6_000),
        }
        for earnings in range(10_000, 60_000, 5_000)
    ],
}


def situation(population):
    year = population["year"]
    people, benunits, groups = {}, {}, {}
    for h, household in enumerate(population["households"]):
        members = []
        for a, person in enumerate(household["adults"]):
            name = f"h{h}_a{a}"
            people[name] = {key: {year: value} for key, value in person.items()}
            members.append(name)
        for c in range(household["children"]):
            name = f"h{h}_c{c}"
            people[name] = {"age": {year: 8}}
            members.append(name)
        benunits[f"b{h}"] = {
            "members": members,
            "would_claim_uc": {year: household["would_claim_uc"]},
        }
        groups[f"h{h}"] = {
            "members": members,
            **{key: {year: value} for key, value in household["household"].items()},
        }
    return {"people": people, "benunits": benunits, "households": groups}


def household_values(sim, variable, year):
    values = np.asarray(sim.calculate(variable, year), dtype=float)
    entity = sim.tax_benefit_system.get_variable(variable).entity.key
    if entity == "household":
        return values
    return np.asarray(sim.map_result(values, entity, "household"), dtype=float)


def run(population):
    year = population["year"]
    sim = Simulation(situation=situation(population))
    names = [
        BEFORE_RESET,
        "hbai_household_net_income",
        "real_hbai_household_net_income",
        "inflation_adjustment",
        "hbai_household_net_income_ahc",
        "equiv_hbai_household_net_income",
        "equiv_hbai_household_net_income_ahc",
        "household_equivalisation_bhc",
        "household_equivalisation_ahc",
        "household_weight",
        "household_count_people",
        "poverty_line_bhc",
        "poverty_line_ahc",
        "poverty_line",
        "deep_poverty_line",
        "poverty_threshold_bhc",
        "poverty_threshold_ahc",
        "poverty_gap_bhc",
        "poverty_gap_ahc",
        "poverty_gap",
        "deep_poverty_gap",
        "in_poverty_bhc",
        "in_poverty_ahc",
        "in_deep_poverty_bhc",
        "in_deep_poverty_ahc",
        "in_poverty",
        "in_deep_poverty",
        "in_relative_poverty_bhc",
        "in_relative_poverty_ahc",
        "household_income_decile",
    ]
    values = {name: household_values(sim, name, year) for name in names}
    values["housing_costs"] = sum(
        household_values(sim, name, year) for name in HOUSING_COSTS
    )
    values["components"] = sum(
        household_values(sim, name, year) for name in HBAI_HOUSEHOLD_NET_INCOME_ADDS
    ) - sum(
        household_values(sim, name, year)
        for name in HBAI_HOUSEHOLD_NET_INCOME_SUBTRACTS
    )
    return values, sim


def person_median(income, v):
    weights = v["household_weight"] * v["household_count_people"]
    return float(MicroSeries(income, weights=weights).median())


@PROPERTY_SETTINGS
@example(PINNED)
@example(PINNED_FEW_AT_ZERO)
@given(populations())
def test_reset_income_and_its_measures(population):
    v, _ = run(population)
    b = v[BEFORE_RESET]
    reset = np.maximum(0, b)

    # 1. The reset, and the measures built on it.
    assert np.allclose(v["hbai_household_net_income"], reset, atol=0.01)
    assert np.all(v["hbai_household_net_income"] >= 0)
    assert np.all(v["equiv_hbai_household_net_income"] >= 0)
    assert np.allclose(
        v["equiv_hbai_household_net_income"],
        reset / v["household_equivalisation_bhc"],
        atol=0.01,
    )
    assert np.allclose(
        v["real_hbai_household_net_income"],
        reset * v["inflation_adjustment"],
        atol=0.5,
    )

    # 2. Differential: the components summed outside the model.
    assert np.allclose(b, v["components"], atol=1)

    # 3. After housing costs, from the reset income.
    ahc = reset - v["housing_costs"]
    assert np.allclose(v["hbai_household_net_income_ahc"], ahc, atol=0.5)
    assert np.allclose(
        v["equiv_hbai_household_net_income_ahc"],
        ahc / v["household_equivalisation_ahc"],
        atol=0.5,
    )
    assert np.all(v["hbai_household_net_income_ahc"] >= -v["housing_costs"] - 0.5)

    # 6. Means: the reset adds exactly the negative parts of b.
    w = v["household_weight"]
    assert np.isclose(
        np.sum(w * v["hbai_household_net_income"]) - np.sum(w * b),
        np.sum(w * np.maximum(0, -b)),
        atol=1,
    )


@PROPERTY_SETTINGS
@example(PINNED)
@example(PINNED_FEW_AT_ZERO)
@given(populations())
def test_poverty_headcounts_are_unchanged_and_gaps_measured_from_the_reset(
    population,
):
    v, _ = run(population)
    b = v[BEFORE_RESET]
    reset = np.maximum(0, b)
    hc = v["housing_costs"]
    equiv_bhc = b / v["household_equivalisation_bhc"]
    equiv_ahc = (b - hc) / v["household_equivalisation_ahc"]

    # 4. Absolute and deep poverty flags: the same before and after the reset.
    assert np.array_equal(v["in_poverty_bhc"], equiv_bhc < v["poverty_threshold_bhc"])
    assert np.array_equal(v["in_poverty_ahc"], equiv_ahc < v["poverty_threshold_ahc"])
    assert np.array_equal(
        v["in_deep_poverty_bhc"], equiv_bhc < v["poverty_threshold_bhc"] / 2
    )
    assert np.array_equal(
        v["in_deep_poverty_ahc"], equiv_ahc < v["poverty_threshold_ahc"] / 2
    )
    assert np.array_equal(v["in_poverty"], b < v["poverty_line"])
    assert np.array_equal(v["in_deep_poverty"], b < v["deep_poverty_line"])

    # 4. Relative poverty, while fewer than half of people are at or below
    # zero before the reset (otherwise the median itself is reset).
    median_bhc = person_median(equiv_bhc, v)
    if median_bhc > 0:
        assert np.array_equal(
            v["in_relative_poverty_bhc"], equiv_bhc < 0.6 * median_bhc
        )
    else:
        # The median is reset to zero with everyone else, so the line is zero
        # and no reset income is below it.
        assert not np.any(v["in_relative_poverty_bhc"])
    median_ahc = person_median(equiv_ahc, v)
    if median_ahc > 0:
        assert np.array_equal(
            v["in_relative_poverty_ahc"], equiv_ahc < 0.6 * median_ahc
        )

    # 5. Gaps from the reset income: never more than the gap before the reset,
    # equal to it when b >= 0, and the BHC gaps never more than their line.
    for gap, line, income, before in [
        ("poverty_gap_bhc", "poverty_line_bhc", reset, b),
        ("poverty_gap", "poverty_line", reset, b),
        ("deep_poverty_gap", "deep_poverty_line", reset, b),
        ("poverty_gap_ahc", "poverty_line_ahc", reset - hc, b - hc),
    ]:
        expected = np.maximum(0, v[line] - income)
        assert np.allclose(v[gap], expected, atol=0.5), gap
        unreset_gap = np.maximum(0, v[line] - before)
        assert np.all(v[gap] <= unreset_gap + 0.5), gap
        assert np.allclose(v[gap][b >= 0], unreset_gap[b >= 0], atol=0.5), gap
    for gap, line in [
        ("poverty_gap_bhc", "poverty_line_bhc"),
        ("poverty_gap", "poverty_line"),
        ("deep_poverty_gap", "deep_poverty_line"),
    ]:
        assert np.all(v[gap] <= v[line] + 0.5), gap


@PROPERTY_SETTINGS
@example(PINNED)
@example(PINNED_FEW_AT_ZERO)
@given(populations())
def test_every_household_has_a_decile_that_rises_with_income(population):
    v, _ = run(population)
    decile = v["household_income_decile"]
    income = v["equiv_hbai_household_net_income"]

    # 7. No household is left out of the deciles, and a lower income never
    # has a higher decile.
    assert np.all((decile >= 1) & (decile <= 10))
    lower = income[:, None] < income[None, :]
    assert not np.any(lower & (decile[:, None] > decile[None, :]))

    # Households at zero (every reset household among them) share the lowest
    # decile, which is decile 1 when they hold less than a tenth of people.
    zero = income == 0
    if zero.any():
        assert np.all(decile[zero] == decile.min())
        people = v["household_weight"] * v["household_count_people"]
        if people[zero].sum() / people.sum() < 0.1 - 1e-6:
            assert np.all(decile[zero] == 1)


def test_labour_supply_responses_default_to_the_income_before_the_reset():
    for function in [
        labour_supply.apply_labour_supply_responses,
        labour_supply.apply_progression_responses,
        progression.calculate_derivative,
        progression.calculate_relative_income_change,
        progression.calculate_derivative_change,
    ]:
        default = inspect.signature(function).parameters["target_variable"].default
        assert default == BEFORE_RESET, function.__name__


def test_a_pay_rise_below_zero_raises_the_income_before_the_reset():
    # 8. A worker whose maintenance payments exceed their pay: b is negative,
    # so the reset income is zero both before and after a pay rise. Measured
    # on b, the rise is kept net of tax and NICs; measured on the reset income
    # it would look fully withdrawn.
    year = 2026
    population = {
        "year": year,
        "households": [
            {
                "adults": [adult(40, 20_000, maintenance=40_000)],
                "children": 0,
                "would_claim_uc": False,
                "household": home(1_200, rent=9_000),
            }
        ],
    }
    sim = Simulation(situation=situation(population))
    assert sim.calculate(BEFORE_RESET, year)[0] < 0
    kept = progression.calculate_derivative(sim, year=year, count_adults=1)
    reset_kept = progression.calculate_derivative(
        sim, target_variable="hbai_household_net_income", year=year, count_adults=1
    )
    # Basic-rate Income Tax and main-rate Class 1 NICs: 20% + 8%.
    assert np.isclose(kept[0], 0.72, atol=0.01)
    assert reset_kept[0] == 0
