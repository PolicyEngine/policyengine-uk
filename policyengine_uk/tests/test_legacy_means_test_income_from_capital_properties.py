"""Property-based tests for income derived from capital in the legacy means tests.

Income Support, Housing Benefit, Pension Credit and council tax reduction
treat rent, interest and dividends as capital, not income (IS Regs 1987 reg
48(4) and Sch 9 para 22; HB Regs 2006 reg 46(4) and Sch 5 para 17; HB (SPC)
Regs 2006 Sch 5 para 22; SPC Regs 2002 Sch IV para 18), and disregard tax only
on income they take into account. Rent for letting part of the home stays
income, less £20 a week per occupier.

Invariants, for any generated population of families:

1. Invariance: scaling property, savings interest and dividend income (by 0
   and 3) changes none of the four means-test incomes, and none of
   Income Support, Housing Benefit, Pension Credit or council tax reduction.
   Universal Credit and tax credits, which have their own income rules, are
   held fixed. Incomes are kept within the basic rate band, where extra
   income from capital cannot change the tax on other income through the
   personal allowance taper or the High Income Child Benefit Charge.
   Marriage Allowance is held at nil: whether a spouse can transfer it
   depends on their income including income from capital, which is a
   legitimate way for income from capital to change the tax on counted
   income.
2. Bounds: the counted home-letting income is between nil and the rent, and
   equals the rent less £20 a week, floored at nil.
3. Monotone: more rent from part of the home never lowers a means-test income
   and never raises Income Support, Housing Benefit, Pension Credit or council
   tax reduction.
4. Tax: legacy_means_test_income_tax is between nil and both income tax and
   the tax on counted income before reductions (earned_income_tax), and
   equals income tax when there is no savings, dividend or property income
   and no Step 7 charge.
5. Tariff: the council tax reduction tariff income that replaces the actual
   income from capital is never negative, never more than the yield at the
   16,000 capital limit (40 steps of 250 at 4.35 a month, 2,088 a year), nil
   outside the national schemes (Northern Ireland, and English people under
   pension age, whose local schemes set their own), and never falls when
   savings rise while the family stays on the same route.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

PROPERTY_SETTINGS = settings(
    max_examples=8,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
YEARS = [2025, 2026]
REGIONS = ["NORTH_EAST", "LONDON", "WALES", "SCOTLAND", "NORTHERN_IRELAND"]
TENURES = ["RENT_FROM_COUNCIL", "RENT_PRIVATELY", "OWNED_OUTRIGHT"]
PENSION_AGE = st.integers(67, 95)
WORKING_AGE = st.integers(18, 60)
SHAPES = {
    "single_pension": [("adult", PENSION_AGE)],
    "couple_pension": [("adult", PENSION_AGE), ("adult", PENSION_AGE)],
    "single_working": [("adult", WORKING_AGE)],
    "couple_working": [("adult", WORKING_AGE), ("adult", WORKING_AGE)],
    "lone_parent": [("adult", WORKING_AGE), ("child", st.integers(0, 5))],
}
MEANS_TEST_INCOMES = [
    "income_support_applicable_income",
    "housing_benefit_applicable_income",
    "pension_credit_income",
    "council_tax_reduction_applicable_income",
]
AWARDS = ["income_support", "housing_benefit", "pension_credit", "council_tax_benefit"]
# Each adult's earnings plus pensions stay below £22,000 and each income from
# capital below £2,000, so even at three times the capital income an adult's
# income stays inside the basic rate band.
small = st.floats(0, 2_000, allow_nan=False, allow_infinity=False)


@st.composite
def adults(draw, age):
    return dict(
        age=age,
        employment_income=draw(st.one_of(st.just(0.0), st.floats(0, 12_000))),
        state_pension=draw(st.floats(0, 10_000)) if age >= 67 else 0.0,
        private_pension_income=draw(st.one_of(st.just(0.0), st.floats(0, 2_000))),
        property_income=draw(st.one_of(st.just(0.0), small)),
        savings_interest_income=draw(st.one_of(st.just(0.0), small)),
        dividend_income=draw(st.one_of(st.just(0.0), small)),
        sublet_income=draw(st.one_of(st.just(0.0), st.floats(0, 8_000))),
    )


@st.composite
def families(draw):
    shape = draw(st.sampled_from(sorted(SHAPES)))
    members = []
    for role, age in SHAPES[shape]:
        a = draw(age)
        members.append((role, draw(adults(a)) if role == "adult" else dict(age=a)))
    return dict(
        shape=shape,
        members=members,
        region=draw(st.sampled_from(REGIONS)),
        tenure=draw(st.sampled_from(TENURES)),
        rent=draw(st.floats(0, 15_000)),
        savings=draw(st.one_of(st.just(0.0), st.floats(0, 20_000))),
        reported=draw(st.booleans()),
        universal_credit=draw(st.sampled_from([0.0, 3_000.0])),
    )


populations = st.lists(families(), min_size=1, max_size=4)


def situation(
    units, year, capital_income_scale=1.0, sublet_extra=0.0, savings_extra=0.0
):
    people, benunits, households = {}, {}, {}
    for i, unit in enumerate(units):
        names = []
        for j, (role, attrs) in enumerate(unit["members"]):
            name = f"p{i}_{j}"
            person = {"age": {year: attrs["age"]}}
            if role == "adult":
                for k, v in attrs.items():
                    if k == "age":
                        continue
                    if k in (
                        "property_income",
                        "savings_interest_income",
                        "dividend_income",
                    ):
                        v = v * capital_income_scale
                    if k == "sublet_income" and j == 0:
                        v = v + sublet_extra
                    person[k] = {year: v}
                person["marriage_allowance"] = {year: 0.0}
                if j == 0 and unit["reported"]:
                    person["income_support_reported"] = {year: 1.0}
                    person["housing_benefit_reported"] = {year: 1.0}
            people[name] = person
            names.append(name)
        benunits[f"b{i}"] = {
            "members": names,
            # Universal Credit and tax credits have their own income rules and
            # are held fixed here.
            "universal_credit": {year: unit["universal_credit"]},
            "tax_credits": {year: 0.0},
            "would_claim_uc": {year: False},
        }
        households[f"h{i}"] = {
            "members": names,
            "region": {year: unit["region"]},
            "tenure_type": {year: unit["tenure"]},
            "rent": {year: unit["rent"]},
            "savings": {year: unit["savings"] + savings_extra},
            "council_tax": {year: 1_500.0},
        }
    return {"people": people, "benunits": benunits, "households": households}


def calculate(units, year, variables, **kwargs):
    sim = Simulation(situation=situation(units, year, **kwargs))
    return {v: np.asarray(sim.calculate(v, year), dtype=float) for v in variables}


@PROPERTY_SETTINGS
@given(populations, st.sampled_from(YEARS))
def test_income_from_capital_changes_no_legacy_means_test(units, year):
    variables = MEANS_TEST_INCOMES + AWARDS
    base = calculate(units, year, variables)
    for scale in (0.0, 3.0):
        scaled = calculate(units, year, variables, capital_income_scale=scale)
        for v in variables:
            np.testing.assert_allclose(
                scaled[v], base[v], atol=0.01, err_msg=f"{v} at scale {scale}"
            )


@PROPERTY_SETTINGS
@given(populations, st.sampled_from(YEARS + [2007]))
def test_home_letting_income_bounds(units, year):
    sim = Simulation(situation=situation(units, year))
    counted = np.asarray(sim.calculate("legacy_benefits_home_letting_income", year))
    rent = np.asarray(sim.calculate("sublet_income", year, map_to="benunit"))
    pension_age = np.asarray(sim.calculate("is_SP_age", year, map_to="benunit")) > 0
    disregard = 20 if year >= 2009 else np.where(pension_age, 20, 4)
    assert np.all(counted >= 0)
    assert np.all(counted <= rent + 0.01)
    np.testing.assert_allclose(
        counted, np.maximum(0, rent / 52 - disregard) * 52, atol=0.01
    )


@PROPERTY_SETTINGS
@given(populations, st.sampled_from(YEARS), st.floats(1, 10_000))
def test_home_letting_rent_is_monotone(units, year, extra):
    variables = MEANS_TEST_INCOMES + AWARDS
    base = calculate(units, year, variables)
    more = calculate(units, year, variables, sublet_extra=extra)
    for v in MEANS_TEST_INCOMES:
        assert np.all(more[v] >= base[v] - 0.01), v
    for v in AWARDS:
        assert np.all(more[v] <= base[v] + 0.01), v


@PROPERTY_SETTINGS
@given(populations, st.sampled_from(YEARS))
def test_legacy_means_test_income_tax_bounds(units, year):
    variables = [
        "legacy_means_test_income_tax",
        "income_tax",
        "earned_income_tax",
        "savings_income_tax",
        "dividend_income_tax",
        "property_income_tax",
    ]
    v = calculate(units, year, variables)
    tax = v["legacy_means_test_income_tax"]
    assert np.all(tax >= 0)
    assert np.all(tax <= v["income_tax"] + 0.01)
    assert np.all(tax <= v["earned_income_tax"] + 0.01)
    no_capital_tax = (
        v["savings_income_tax"] + v["dividend_income_tax"] + v["property_income_tax"]
    ) == 0
    np.testing.assert_allclose(tax[no_capital_tax], v["income_tax"][no_capital_tax])
    without = calculate(
        units,
        year,
        ["income_tax", "legacy_means_test_income_tax"],
        capital_income_scale=0.0,
    )
    np.testing.assert_allclose(
        without["legacy_means_test_income_tax"], without["income_tax"], atol=0.01
    )


MAXIMUM_TARIFF_INCOME = 40 * 4.35 * 12
ENGLISH_REGIONS = {"NORTH_EAST", "LONDON"}


@PROPERTY_SETTINGS
@given(populations, st.sampled_from(YEARS), st.floats(1, 20_000))
def test_council_tax_reduction_tariff_income_is_bounded_and_monotone(
    units, year, extra
):
    variables = [
        "council_tax_reduction_tariff_income",
        "council_tax_reduction_pensioner",
        "in_receipt_of_guarantee_credit",
        "in_receipt_of_savings_credit_only",
    ]
    base = calculate(units, year, variables)
    more = calculate(units, year, variables, savings_extra=extra)
    tariff = base["council_tax_reduction_tariff_income"]
    assert np.all(tariff >= 0)
    assert np.all(tariff <= MAXIMUM_TARIFF_INCOME + 0.01)
    region = np.array([unit["region"] for unit in units])
    pensioner = base["council_tax_reduction_pensioner"].astype(bool)
    outside_national_schemes = (region == "NORTHERN_IRELAND") | (
        np.isin(region, list(ENGLISH_REGIONS)) & ~pensioner
    )
    assert np.all(tariff[outside_national_schemes] == 0)

    def route(values):
        return (
            values["council_tax_reduction_pensioner"].astype(int) * 4
            + values["in_receipt_of_guarantee_credit"].astype(int) * 2
            + values["in_receipt_of_savings_credit_only"].astype(int)
        )

    same_route = route(base) == route(more)
    assert np.all(
        more["council_tax_reduction_tariff_income"][same_route]
        >= tariff[same_route] - 0.01
    )
