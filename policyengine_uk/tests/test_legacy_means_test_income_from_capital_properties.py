"""Property-based tests for income derived from capital in the legacy means tests.

Income Support, Housing Benefit, Pension Credit and council tax reduction
treat rent, interest and dividends as capital, not income (IS Regs 1987 reg
48(4) and Sch 9 para 22; HB Regs 2006 reg 46(4) and Sch 5 para 17; HB (SPC)
Regs 2006 Sch 5 para 22; SPC Regs 2002 Sch IV para 18), and disregard tax only
on income they take into account. Rent for letting part of the home stays
income, less £20 a week per occupier.

Invariants, for any generated population of families:

1. Invariance: where nobody in the population has employed earnings or
   self-employment income, scaling property, savings interest and dividend
   income (by 0 and 3) changes none of the four means-test incomes, and none
   of Income Support, Housing Benefit, Pension Credit or council tax
   reduction. Universal Credit and tax credits, which have their own income
   rules, are held fixed. Incomes are kept within the basic rate band, where
   extra income from capital cannot change the tax on other income through
   the personal allowance taper or the High Income Child Benefit Charge.
   Marriage Allowance is held at nil: whether a spouse can transfer it
   depends on their income including income from capital, which is a
   legitimate way for income from capital to change the tax on counted
   income.
   Intended exception: earnings carry the extra tax they cause, including on
   savings, dividends and rent, in all four tests. With
   earnings, income from capital can move that tax: earnings under the
   personal allowance can leave rent or dividends taxable. Where someone has
   earnings, each means-test income changes by exactly minus the change in
   the tax that test deducts (legacy_means_test_deducted_income_tax, summed
   over the members it counts) and in its earnings disregard, which is
   capped at net earnings, unless floored or on a route that does not use
   the test's own income rules. The awards are compared wherever none of
   those taxes or disregards moves.
2. Bounds: the counted home-letting income is between nil and the rent, and
   equals the rent less £20 a week, floored at nil.
3. Monotone: more rent from part of the home never lowers a means-test income
   and never raises Income Support, Housing Benefit, Pension Credit or council
   tax reduction.
4. Tax: legacy_means_test_income_tax, the Step 4 split the tests read
   without earnings, is between nil and both income tax and the tax on
   counted income before reductions (earned_income_tax), and equals income
   tax when there is no savings, dividend or property income and no Step 7
   charge. The tax each test deducts (legacy_means_test_deducted_income_tax)
   is between nil and the income tax before the winter fuel payment charge;
   it equals that tax when nobody has savings, dividend or property income
   and no Step 7 charge applies; and without earnings it equals
   legacy_means_test_income_tax, except where the nil floor on the tax on
   uncounted income binds. Within the basic rate band it is never below
   legacy_means_test_income_tax: earnings never lower the tax on income from
   capital there. Each test floors the sum of the deduction over the members
   it counts at nil.
5. Tariff: the council tax reduction tariff income that replaces the actual
   income from capital is never negative, never more than the yield at the
   16,000 capital limit (40 steps of 250 at 4.35 a month, 2,088 a year), nil
   outside the national schemes (Northern Ireland, and English people under
   pension age, whose local schemes set their own), and never falls when
   savings rise while the family stays on the same route (pensioner, UC
   award, passport, guarantee credit, savings credit only).
6. Differential: for every generated family without self-employment income,
   Income Support, Housing Benefit and the council tax reduction line deduct,
   for each person they count, the same income tax as Pension Credit's tax
   line: the pre-charge income tax less
   legacy_means_test_uncounted_income_tax_without_earnings.
7. Applicant: where the household head does not apply alone for council tax
   reduction, council_tax_reduction_home_letting_income equals
   legacy_benefits_home_letting_income; where the head applies alone, her
   council tax reduction income moves with her own rent from letting part of
   the home and not with anyone else's.
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


@st.composite
def taxed_adults(draw, age):
    """Adults whose pensions use up the personal allowance and whose income
    from capital reaches about 20,000, so that it bears tax without
    earnings."""
    return dict(
        age=age,
        employment_income=0.0,
        state_pension=draw(st.floats(0, 10_000)) if age >= 67 else 0.0,
        private_pension_income=draw(st.floats(12_570, 20_000)),
        property_income=draw(st.floats(0, 20_000)),
        savings_interest_income=draw(st.floats(2_000, 20_000)),
        dividend_income=draw(st.floats(0, 20_000)),
        sublet_income=0.0,
    )


@st.composite
def taxed_families(draw):
    family = draw(families())
    members = [
        (role, draw(taxed_adults(attrs["age"])) if role == "adult" else attrs)
        for role, attrs in family["members"]
    ]
    return dict(family, members=members)


taxed_populations = st.lists(taxed_families(), min_size=1, max_size=4)


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


# The members whose income and tax each test counts.
TEST_MEMBERS = {
    "income_support_applicable_income": "is_claimant_or_partner",
    "housing_benefit_applicable_income": "is_claimant_or_partner",
    "pension_credit_income": "is_claimant_or_partner",
    "council_tax_reduction_applicable_income": (
        "is_council_tax_reduction_applicant_or_partner"
    ),
}
# Each test's earnings disregard, which is capped at net earnings, so it moves
# with the tax on them.
EARNINGS_DISREGARDS = {
    "income_support_applicable_income": "income_support_earnings_disregard",
    "housing_benefit_applicable_income": "housing_benefit_applicable_income_disregard",
    "pension_credit_income": "pension_credit_earnings_disregard",
    "council_tax_reduction_applicable_income": (
        "council_tax_reduction_pensioner_earnings_disregard"
    ),
}
EARNINGS = ["employment_income", "self_employment_income"]


def calculate_with_taxes(units, year, variables, **kwargs):
    """Benefit-unit values of ``variables``, each test's deducted tax summed
    over the members it counts (keyed ``tax:<income>``), and whether anyone in
    the unit has earnings (``earners``)."""
    sim = Simulation(situation=situation(units, year, **kwargs))
    out = {v: np.asarray(sim.calculate(v, year), dtype=float) for v in variables}
    tax = np.asarray(
        sim.calculate("legacy_means_test_deducted_income_tax", year), dtype=float
    )
    for income, members in TEST_MEMBERS.items():
        mask = np.asarray(sim.calculate(members, year), dtype=float)
        out[f"tax:{income}"] = sim.map_result(tax * mask, "person", "benunit")
    earnings = sum(
        np.abs(np.asarray(sim.calculate(v, year), dtype=float)) for v in EARNINGS
    )
    out["earners"] = sim.map_result(earnings, "person", "benunit") > 0
    return out


@PROPERTY_SETTINGS
@given(populations, st.sampled_from(YEARS))
def test_income_from_capital_changes_no_legacy_means_test(units, year):
    disregards = sorted(set(EARNINGS_DISREGARDS.values()))
    routes = [
        "council_tax_reduction_universal_credit_award",
        "housing_benefit_on_passporting_benefit",
    ]
    variables = MEANS_TEST_INCOMES + AWARDS + disregards + routes
    base = calculate_with_taxes(units, year, variables)
    for scale in (0.0, 3.0):
        scaled = calculate_with_taxes(
            units, year, variables, capital_income_scale=scale
        )
        moved = {
            income: (scaled[f"tax:{income}"] - base[f"tax:{income}"])
            + (scaled[EARNINGS_DISREGARDS[income]] - base[EARNINGS_DISREGARDS[income]])
            for income in MEANS_TEST_INCOMES
        }
        steady = np.all(
            [np.abs(moved[income]) < 0.01 for income in MEANS_TEST_INCOMES], axis=0
        )
        # Without earnings, the tax each test deducts does not move.
        assert np.all(steady[~base["earners"]])
        # Where the deducted tax is steady, nothing moves.
        for v in MEANS_TEST_INCOMES + AWARDS:
            np.testing.assert_allclose(
                scaled[v][steady],
                base[v][steady],
                atol=0.01,
                err_msg=f"{v} at scale {scale}",
            )
        # Intended exception (d1424): where earnings make it move, each
        # means-test income moves by exactly minus that change, wherever
        # neither run is floored and the test uses its own income rules.
        pension_credit_route = (base["pension_credit"] > 0) | (
            scaled["pension_credit"] > 0
        )
        own_rules = {
            "income_support_applicable_income": np.ones_like(steady),
            "pension_credit_income": np.ones_like(steady),
            "housing_benefit_applicable_income": ~pension_credit_route
            & (base["housing_benefit_on_passporting_benefit"] == 0),
            "council_tax_reduction_applicable_income": ~pension_credit_route
            & (base["council_tax_reduction_universal_credit_award"] == 0),
        }
        for income in MEANS_TEST_INCOMES:
            checked = (
                ~steady & own_rules[income] & (base[income] > 0) & (scaled[income] > 0)
            )
            np.testing.assert_allclose(
                (scaled[income] - base[income])[checked],
                -moved[income][checked],
                atol=0.01,
                err_msg=f"{income} decomposition at scale {scale}",
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
        "legacy_means_test_deducted_income_tax",
        "legacy_means_test_uncounted_income_tax_without_earnings",
        "income_tax",
        "income_tax_before_winter_fuel_payment_charge",
        "income_tax_charges",
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

    # The tax each test deducts.
    deducted = v["legacy_means_test_deducted_income_tax"]
    pre_charge = v["income_tax_before_winter_fuel_payment_charge"]
    assert np.all(deducted >= -0.01)
    assert np.all(deducted <= pre_charge + 0.01)
    # Within the basic rate band, earnings never lower the tax on income
    # from capital, so the deduction is never below the Step 4 split.
    assert np.all(deducted >= tax - 0.01)

    # Nobody has savings, dividend or property income: it is the pre-charge
    # tax wherever no Step 7 charge applies.
    without_capital = calculate(units, year, variables, capital_income_scale=0.0)
    no_charge = without_capital["income_tax_charges"] == 0
    np.testing.assert_allclose(
        without_capital["legacy_means_test_deducted_income_tax"][no_charge],
        without_capital["income_tax_before_winter_fuel_payment_charge"][no_charge],
        atol=0.01,
    )
    np.testing.assert_allclose(
        without_capital["legacy_means_test_income_tax"],
        without_capital["income_tax"],
        atol=0.01,
    )


@PROPERTY_SETTINGS
@given(taxed_populations, st.sampled_from(YEARS))
def test_deducted_tax_without_earnings_is_the_step_4_split(units, year):
    """Nobody has earnings, and every adult's interest exceeds the personal
    savings allowance on top of a pension that uses up the personal
    allowance, so the tax on uncounted income is positive and the deduction
    must leave all of it out."""
    v = calculate(
        units,
        year,
        [
            "legacy_means_test_income_tax",
            "legacy_means_test_deducted_income_tax",
            "legacy_means_test_uncounted_income_tax_without_earnings",
            "income_tax_before_winter_fuel_payment_charge",
        ],
    )
    assert (v["legacy_means_test_uncounted_income_tax_without_earnings"] > 0).any()
    # Equal unless the nil floor on the tax on uncounted income binds, where
    # the Step 4 split exceeds the pre-charge tax and the deduction is the
    # pre-charge tax.
    np.testing.assert_allclose(
        v["legacy_means_test_deducted_income_tax"],
        np.minimum(
            v["legacy_means_test_income_tax"],
            v["income_tax_before_winter_fuel_payment_charge"],
        ),
        atol=0.01,
    )
    floor_binds = (
        v["legacy_means_test_income_tax"]
        > v["income_tax_before_winter_fuel_payment_charge"] + 0.01
    )
    np.testing.assert_allclose(
        v["legacy_means_test_deducted_income_tax"][~floor_binds],
        v["legacy_means_test_income_tax"][~floor_binds],
        atol=0.01,
    )


@PROPERTY_SETTINGS
@given(populations, st.sampled_from(YEARS))
def test_the_four_tests_deduct_the_same_income_tax(units, year):
    """Income Support, Housing Benefit and the council tax reduction line
    deduct, for each person they count, the income tax Pension Credit's tax
    line deducts. Each test's income is recomputed with the person's income
    tax raised by one pound and compared with the original, so the check
    reads each formula rather than the shared variable. The families have no
    self-employment income, where Pension Credit's notional tax applies."""
    sim = Simulation(situation=situation(units, year))
    people = sim.populations["person"].count
    pension_credit_tax = np.asarray(
        sim.calculate("income_tax_before_winter_fuel_payment_charge", year)
    ) - np.asarray(
        sim.calculate("legacy_means_test_uncounted_income_tax_without_earnings", year)
    )
    np.testing.assert_allclose(
        np.asarray(sim.calculate("legacy_means_test_deducted_income_tax", year)),
        pension_credit_tax,
        atol=0.01,
    )
    # Each test's income responds one-for-one to the shared deduction for the
    # members it counts, and not at all to the Step 4 split.
    bumped = Simulation(situation=situation(units, year))
    bumped.set_input(
        "legacy_means_test_deducted_income_tax",
        year,
        np.asarray(sim.calculate("legacy_means_test_deducted_income_tax", year)) + 1.0,
    )
    split = Simulation(situation=situation(units, year))
    split.set_input(
        "legacy_means_test_income_tax",
        year,
        np.asarray(sim.calculate("legacy_means_test_income_tax", year)) + 1.0,
    )
    split.set_input(
        "legacy_means_test_deducted_income_tax",
        year,
        np.asarray(sim.calculate("legacy_means_test_deducted_income_tax", year)),
    )
    assert people > 0
    for income, members in TEST_MEMBERS.items():
        base = np.asarray(sim.calculate(income, year), dtype=float)
        counted = sim.map_result(
            np.asarray(sim.calculate(members, year), dtype=float), "person", "benunit"
        )
        moved = np.asarray(bumped.calculate(income, year), dtype=float)
        unfloored = (base > 1) & (moved > 0)
        own_rules = (np.asarray(sim.calculate("pension_credit", year)) == 0) | (
            income == "pension_credit_income"
        )
        if income == "housing_benefit_applicable_income":
            own_rules &= (
                np.asarray(
                    sim.calculate("housing_benefit_on_passporting_benefit", year)
                )
                == 0
            )
        if income == "council_tax_reduction_applicable_income":
            own_rules &= (
                np.asarray(
                    sim.calculate("council_tax_reduction_universal_credit_award", year)
                )
                == 0
            )
        checked = unfloored & own_rules
        # The earnings disregard is capped at net earnings, so it can fall
        # with them.
        disregard = EARNINGS_DISREGARDS[income]
        disregard_change = np.asarray(
            bumped.calculate(disregard, year), dtype=float
        ) - np.asarray(sim.calculate(disregard, year), dtype=float)
        np.testing.assert_allclose(
            (base - moved)[checked],
            (counted + disregard_change)[checked],
            atol=0.01,
            err_msg=income,
        )
        np.testing.assert_allclose(
            np.asarray(split.calculate(income, year), dtype=float),
            base,
            atol=0.01,
            err_msg=f"{income} reads the Step 4 split",
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
        "council_tax_reduction_universal_credit_award",
        "council_tax_reduction_relevant_income_based_benefit",
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
            values["council_tax_reduction_pensioner"].astype(int) * 16
            + values["council_tax_reduction_universal_credit_award"].astype(int) * 8
            + values["council_tax_reduction_relevant_income_based_benefit"].astype(int)
            * 4
            + values["in_receipt_of_guarantee_credit"].astype(int) * 2
            + values["in_receipt_of_savings_credit_only"].astype(int)
        )

    same_route = route(base) == route(more)
    assert np.all(
        more["council_tax_reduction_tariff_income"][same_route]
        >= tariff[same_route] - 0.01
    )


@PROPERTY_SETTINGS
@given(populations, st.sampled_from(YEARS))
def test_council_tax_reduction_letting_income_matches_the_legacy_measure(units, year):
    """7. Applicant. Where the household head does not apply alone, the
    council tax reduction applicant and partner are the benefit unit's
    claimant and partner, so council_tax_reduction_home_letting_income equals
    legacy_benefits_home_letting_income. (The two use different pension-age
    tests, but the working-age and pension-age disregards have been equal
    since April 2008.)"""
    v = calculate(
        units,
        year,
        [
            "council_tax_reduction_head_applies_alone",
            "council_tax_reduction_home_letting_income",
            "legacy_benefits_home_letting_income",
        ],
    )
    family = v["council_tax_reduction_head_applies_alone"] == 0
    np.testing.assert_allclose(
        v["council_tax_reduction_home_letting_income"][family],
        v["legacy_benefits_home_letting_income"][family],
        atol=0.01,
    )


# A household head who applies alone: a liable head sharing a benefit unit
# with a young couple flagged as parents and their baby, so the couple are the
# benefit unit's claimant and partner.
head_alone_household = st.fixed_dictionaries(
    dict(
        head_age=st.integers(40, 95),
        parent_ages=st.tuples(st.integers(16, 17), st.integers(16, 17)),
        head_pension=st.floats(0, 20_000),
        head_wages=st.one_of(st.just(0.0), st.floats(0, 20_000)),
        head_rent=st.one_of(st.just(0.0), st.floats(0, 10_000)),
        parent_rent=st.one_of(st.just(0.0), st.floats(0, 10_000)),
        region=st.sampled_from(REGIONS),
    )
)


def head_alone_situation(households, year, head_extra=0.0, parent_extra=0.0):
    people, benunits, homes = {}, {}, {}
    for i, h in enumerate(households):
        head, mother, father, baby = (f"{r}{i}" for r in "hmfb")
        people[head] = {
            "age": {year: h["head_age"]},
            "is_household_head": {year: True},
            "private_pension_income": {year: h["head_pension"]},
            "employment_income": {year: h["head_wages"]},
            "sublet_income": {year: h["head_rent"] + head_extra},
        }
        people[mother] = {
            "age": {year: h["parent_ages"][0]},
            "is_parent": {year: True},
            "is_household_head": {year: False},
            "sublet_income": {year: h["parent_rent"] + parent_extra},
        }
        people[father] = {
            "age": {year: h["parent_ages"][1]},
            "is_parent": {year: True},
            "is_household_head": {year: False},
        }
        people[baby] = {"age": {year: 0}, "is_household_head": {year: False}}
        members = [head, mother, father, baby]
        benunits[f"b{i}"] = {
            "members": members,
            "would_claim_uc": {year: False},
            "universal_credit": {year: 0.0},
            "tax_credits": {year: 0.0},
        }
        homes[f"h{i}"] = {
            "members": members,
            "region": {year: h["region"]},
            "council_tax": {year: 1_500.0},
            "savings": {year: 0.0},
        }
    return {"people": people, "benunits": benunits, "households": homes}


HEAD_ALONE_VARIABLES = [
    "council_tax_reduction_head_applies_alone",
    "council_tax_reduction_pensioner",
    "council_tax_reduction_home_letting_income",
    "legacy_benefits_home_letting_income",
    "council_tax_reduction_applicable_income",
]


def head_alone_values(households, year, **kwargs):
    sim = Simulation(situation=head_alone_situation(households, year, **kwargs))
    return {
        v: np.asarray(sim.calculate(v, year), dtype=float) for v in HEAD_ALONE_VARIABLES
    }


@PROPERTY_SETTINGS
@given(
    st.lists(head_alone_household, min_size=1, max_size=4),
    st.sampled_from(YEARS),
    st.floats(1, 5_000),
)
def test_a_head_applying_alone_counts_only_her_own_letting_income(
    households, year, extra
):
    """7. Applicant. Where the household head applies alone, she is the
    council tax reduction applicant (SI 2012/2885 reg 2(1), Sch 1 para 11):
    her income moves with her own rent from letting part of the home, by the
    change in council_tax_reduction_home_letting_income wherever the scheme
    counts it, and not with the benefit unit's claimant's or partner's."""
    base = head_alone_values(households, year)
    assert np.all(base["council_tax_reduction_head_applies_alone"] == 1)
    more_own = head_alone_values(households, year, head_extra=extra)
    more_others = head_alone_values(households, year, parent_extra=extra)
    # Scotland's scheme for people under pension age lists no such income
    # (SSI 2021/249 reg 57(1)).
    region = np.array([h["region"] for h in households])
    counts = ~((region == "SCOTLAND") & (base["council_tax_reduction_pensioner"] == 0))
    income = "council_tax_reduction_applicable_income"
    letting = "council_tax_reduction_home_letting_income"
    np.testing.assert_allclose(
        more_own[income] - base[income],
        np.where(counts, more_own[letting] - base[letting], 0),
        atol=0.02,
    )
    assert np.all(more_own[letting] >= base[letting] - 0.01)
    np.testing.assert_allclose(more_others[income], base[income], atol=0.01)
    np.testing.assert_allclose(more_others[letting], base[letting], atol=0.01)
    # The couple's own legacy measure does count it.
    assert np.all(
        more_others["legacy_benefits_home_letting_income"]
        >= base["legacy_benefits_home_letting_income"] - 0.01
    )
