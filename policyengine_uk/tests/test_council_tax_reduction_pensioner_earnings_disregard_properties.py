"""Property-based tests for the pensioner Council Tax Reduction earnings disregards.

SI 2012/2885 Sch 4 (England), WSI 2013/3029 Sch 3 (Wales) and SSI 2012/319
Sch 2 (Scotland) disregard from a pension-age applicant's and partner's net
earnings £25 a week for a lone parent, £10 for a couple and £5 for anyone
else, plus £17.10 where a work condition is met and net earnings at least
equal the other disregards, the deductible childcare charges and £17.10.
Scotland read £37.10 for £17.10 from 6 April 2020 to 4 April 2021 (SSI
2020/108). The sums and the work conditions the model applies correspond to
the Housing Benefit pension-age schedule (SI 2006/214 Sch 4).

Invariants, for any generated population of families:

1. Bounds: 0 <= disregard <= min(net earnings, (£25 + £37.10) x 52); no
   earnings, no disregard; zero for a family that is not one of the schemes'
   pensioners (whatever its ages), and zero in Northern Ireland or where the
   country is unknown.
2. The statutory sums: in every year from 2015 (the first year the model
   simulates) to 2030 and in each nation, a pension-age family with enough
   earnings and no work condition has exactly its weekly sum x 52
   disregarded, £5, £10 or £25; with a work condition, that plus £17.10 x 52
   (£37.10 in Scotland in 2020). The parameters themselves hold those sums,
   without uprating, in every year from 2013-14, when the schemes began.
3. Metamorphic: the disregard is non-decreasing in employment income.
4. The disregard never raises Council Tax Reduction applicable income, lowers
   it by no more than the claimant's and partner's gross earnings, and never
   lowers the award.
5. Differential against Housing Benefit: for pension-age families without
   childcare charges, the CTR disregard equals the Housing Benefit disregard
   in every nation and year, except England and Wales in 2020, where Housing
   Benefit's additional sum was £37.10 (SI 2020/371 reg 5) and CTR's stayed
   £17.10 (an intended difference, which the test pins).
6. The Housing Benefit disregard (#1908) is the statutory weekly sum x 52 in
   every year from 2015 to 2030, at working and pension age: £5, £10 or £25
   (SI 2006/213 Sch 4 paras 4, 7, 10; SI 2006/214 Sch 4 paras 2, 7), plus
   £17.10 (£37.10 in 2020, SI 2020/371 reg 5) where a work condition holds,
   for families with enough earnings and no Income Support, income-based JSA
   or income-related ESA (whose working-age earnings are all disregarded).
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.system import system

WEEKS = 52
PROPERTY_SETTINGS = settings(
    max_examples=5,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
NATIONS = ["ENGLAND", "WALES", "SCOTLAND"]
SHAPES = {
    "single": (1, 0),
    "couple": (2, 0),
    "lone_parent": (1, 2),
    "couple_with_children": (2, 1),
}
WEEKLY = {"single": 5, "couple": 10, "lone_parent": 25, "couple_with_children": 10}
# State Pension age rises from 66 to 67 between 2026 and 2028, so 68 and over
# is pension age in every year tested and 60 and under is working age.
PENSION_AGE = st.integers(68, 90)
ADULT_AGE = st.one_of(st.integers(18, 90), st.sampled_from([24, 25, 60, 68]))
HOURS = st.one_of(
    st.sampled_from([0.0, 15.0, 16.0, 29.0, 30.0]), st.floats(0, 50, allow_nan=False)
)
EARNINGS = st.one_of(
    st.just(0.0),
    st.floats(0, 3_000, allow_nan=False),
    st.floats(0, 60_000, allow_nan=False),
)
MAX_ANNUAL = (25 + 37.1) * WEEKS


def additional_weekly(nation, year):
    return 37.1 if (nation == "SCOTLAND" and year == 2020) else 17.1


@st.composite
def adults(draw, age, earnings):
    return dict(
        age=draw(age),
        employment_income=draw(earnings),
        weekly_hours=draw(HOURS),
        disabled=draw(st.booleans()),
        state_pension=draw(st.one_of(st.just(0.0), st.floats(0, 20_000))),
    )


@st.composite
def families(draw, age=ADULT_AGE, earnings=EARNINGS, nations=NATIONS):
    shape = draw(st.sampled_from(sorted(SHAPES)))
    n_adults, n_children = SHAPES[shape]
    return dict(
        shape=shape,
        nation=draw(st.sampled_from(nations)),
        adults=[draw(adults(age, earnings)) for _ in range(n_adults)],
        children=[draw(st.integers(0, 15)) for _ in range(n_children)],
    )


def situation(units, year, earnings_bump=0.0, no_income_related_benefits=False):
    people, benunits, households = {}, {}, {}
    for i, unit in enumerate(units):
        names = []
        for j, adult in enumerate(unit["adults"]):
            name = f"a{i}_{j}"
            people[name] = {
                "age": {year: adult["age"]},
                "employment_income": {
                    year: adult["employment_income"] + (earnings_bump if j == 0 else 0)
                },
                "weekly_hours": {year: adult["weekly_hours"]},
                "is_disabled_for_benefits": {year: adult["disabled"]},
                "state_pension": {year: adult["state_pension"]},
            }
            names.append(name)
        for k, child_age in enumerate(unit["children"]):
            name = f"c{i}_{k}"
            people[name] = {"age": {year: child_age}}
            names.append(name)
        benunits[f"b{i}"] = {
            "members": names,
            "claims_all_entitled_benefits": {year: True},
        }
        if no_income_related_benefits:
            for benefit in ("income_support", "jsa_income", "esa_income"):
                benunits[f"b{i}"][benefit] = {year: 0.0}
        households[f"h{i}"] = {
            "members": names,
            "country": {year: unit["nation"]},
            "council_tax": {year: 2_000.0},
            "savings": {year: 0.0},
        }
    return {"people": people, "benunits": benunits, "households": households}


VARIABLES = [
    "council_tax_reduction_pensioner_earnings_disregard",
    "housing_benefit_net_earnings",
    "housing_benefit_applicable_income_disregard",
    "meets_housing_benefit_additional_earnings_disregard_conditions",
]


def calculate(units, year=2026, variables=VARIABLES, **kwargs):
    sim = Simulation(situation=situation(units, year, **kwargs))
    return {v: np.asarray(sim.calculate(v, year), dtype=float) for v in variables}


def gross_earnings(unit):
    return sum(max(adult["employment_income"], 0) for adult in unit["adults"])


def working_age(unit):
    return all(adult["age"] <= 60 for adult in unit["adults"])


@PROPERTY_SETTINGS
@given(
    st.lists(
        families(nations=NATIONS + ["NORTHERN_IRELAND", "UNKNOWN"]),
        min_size=1,
        max_size=30,
    )
)
def test_disregard_is_bounded_and_only_for_pension_age_families_in_great_britain(
    units,
):
    values = calculate(units, variables=VARIABLES + ["council_tax_reduction_pensioner"])
    disregard = values["council_tax_reduction_pensioner_earnings_disregard"]
    net = values["housing_benefit_net_earnings"]
    pensioner = values["council_tax_reduction_pensioner"].astype(bool)
    for i, unit in enumerate(units):
        assert disregard[i] >= 0, unit
        assert disregard[i] <= min(net[i], MAX_ANNUAL) + 0.01, unit
        if gross_earnings(unit) == 0:
            assert disregard[i] == 0, unit
        if working_age(unit):
            assert not pensioner[i], unit
        if not pensioner[i] or unit["nation"] in ("NORTHERN_IRELAND", "UNKNOWN"):
            assert disregard[i] == 0, unit


@PROPERTY_SETTINGS
@given(
    st.lists(
        families(age=PENSION_AGE, earnings=st.floats(20_000, 40_000)),
        min_size=1,
        max_size=30,
    ),
    st.integers(2015, 2030),
)
def test_disregard_is_the_statutory_weekly_sum_in_every_year(units, year):
    values = calculate(units, year=year)
    disregard = values["council_tax_reduction_pensioner_earnings_disregard"]
    conditions = values[
        "meets_housing_benefit_additional_earnings_disregard_conditions"
    ].astype(bool)
    for i, unit in enumerate(units):
        weekly = WEEKLY[unit["shape"]]
        if conditions[i]:
            weekly += additional_weekly(unit["nation"], year)
        assert abs(disregard[i] - weekly * WEEKS) < 0.01, (unit, year)


def test_parameters_hold_the_statutory_sums_without_uprating():
    for year in range(2013, 2031):
        # Read in each financial year (30 April, the model's convention for
        # years; an integer year before 2015 reads 1 January instead).
        p = system.parameters(f"{year}-04-30").gov.local_authorities
        for nation in NATIONS:
            sums = getattr(
                p, nation.lower()
            ).council_tax_reduction.pensioners.earnings_disregard
            assert (sums.single, sums.couple, sums.lone_parent) == (5, 10, 25), (
                nation,
                year,
            )
            assert sums.additional == additional_weekly(nation, year), (nation, year)


@PROPERTY_SETTINGS
@given(
    st.lists(families(), min_size=1, max_size=30),
    st.floats(1, 5_000, allow_nan=False, allow_infinity=False),
)
def test_disregard_is_non_decreasing_in_earnings(units, bump):
    key = "council_tax_reduction_pensioner_earnings_disregard"
    before = calculate(units)[key]
    after = calculate(units, earnings_bump=bump)[key]
    for i, unit in enumerate(units):
        assert after[i] >= before[i] - 0.01, (unit, bump)


@PROPERTY_SETTINGS
@given(st.lists(families(), min_size=1, max_size=30))
def test_disregard_lowers_income_by_no_more_than_earnings_and_never_cuts_ctr(units):
    keys = [
        "council_tax_reduction_applicable_income",
        "simulated_council_tax_reduction_benunit",
    ]
    with_disregard = calculate(units, variables=keys)
    sim = Simulation(situation=situation(units, 2026))
    sim.set_input(
        "council_tax_reduction_pensioner_earnings_disregard",
        2026,
        np.zeros(len(units)),
    )
    without = {k: np.asarray(sim.calculate(k, 2026), dtype=float) for k in keys}
    income, award = keys
    for i, unit in enumerate(units):
        assert with_disregard[income][i] <= without[income][i] + 0.01, unit
        drop = without[income][i] - with_disregard[income][i]
        assert drop <= gross_earnings(unit) + 0.01, unit
        assert with_disregard[award][i] >= without[award][i] - 0.01, unit


@PROPERTY_SETTINGS
@given(
    st.lists(families(age=PENSION_AGE), min_size=1, max_size=30),
    st.sampled_from([2019, 2020, 2021, 2026]),
)
def test_differential_against_the_housing_benefit_pension_age_disregard(units, year):
    values = calculate(units, year=year)
    ctr = values["council_tax_reduction_pensioner_earnings_disregard"]
    hb = values["housing_benefit_applicable_income_disregard"]
    net = values["housing_benefit_net_earnings"]
    conditions = values[
        "meets_housing_benefit_additional_earnings_disregard_conditions"
    ].astype(bool)
    for i, unit in enumerate(units):
        if year == 2020 and unit["nation"] != "SCOTLAND":
            # Intended difference: SI 2020/371 raised Housing Benefit's
            # additional sum to £37.10; the English and Welsh CTR rules kept
            # £17.10. Each still gives its own statutory amount.
            flat = min(WEEKLY[unit["shape"]] * WEEKS, net[i])
            for value, additional in ((ctr[i], 17.1), (hb[i], 37.1)):
                expected = flat
                if conditions[i] and round(net[i], 2) >= round(
                    flat + additional * WEEKS, 2
                ):
                    expected += additional * WEEKS
                assert abs(value - expected) < 0.01, (unit, year)
        else:
            assert abs(ctr[i] - hb[i]) < 0.01, (unit, year)


@PROPERTY_SETTINGS
@given(
    st.lists(
        families(earnings=st.floats(20_000, 40_000)),
        min_size=1,
        max_size=30,
    ),
    st.integers(2015, 2030),
)
def test_housing_benefit_disregard_is_the_statutory_weekly_sum_in_every_year(
    units, year
):
    values = calculate(units, year=year, no_income_related_benefits=True)
    disregard = values["housing_benefit_applicable_income_disregard"]
    conditions = values[
        "meets_housing_benefit_additional_earnings_disregard_conditions"
    ].astype(bool)
    for i, unit in enumerate(units):
        weekly = WEEKLY[unit["shape"]]
        if conditions[i]:
            weekly += 37.1 if year == 2020 else 17.1
        assert abs(disregard[i] - weekly * WEEKS) < 0.01, (unit, year)
