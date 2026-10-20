"""Property-based tests for the Marriage Allowance (ITA 2007 ss. 55A-55E).

An election by one spouse or civil partner cuts their own personal allowance
by the transferable amount (s. 55B(6)) and gives the other a Step 6 tax
reduction of the appropriate percentage of it, capped at their Step 5 tax
(s. 55A(2), s. 55B(1), (3), s. 29(2)). The couple elects only when the
conditions allow it and it lowers their combined income tax.

Invariants, for any generated population of couples with every kind of
taxable income, some with residential finance costs, in England, Wales or
Scotland:

1. The couple's income tax is never higher than with no election.
2. Differential against brute force: the model's election gives the lowest
   couple income tax of no election, the first spouse electing and the second
   spouse electing, among those the conditions allow, each run with the
   election fixed.
3. Once a spouse has elected, the gaining partner's reduction, allowance and
   income tax do not depend on the electing spouse's income, and the electing
   spouse's allowance falls by exactly the transferable amount.
4. Accounting: in each couple what one spouse gives up the other receives, at
   most one spouse elects, the gaining partner's tax falls by exactly the
   reduction, and the reduction is at most the appropriate percentage of the
   transferable amount and the tax left to reduce.
5. The couple's income tax, with the election the model makes, never falls
   when either spouse has more income.
6. No one outside a married couple gives up or receives anything.
7. Differential against the tax bands: outside Scotland, with no dividends or
   property income, a person meets the income conditions exactly when the
   model's own band variables put none of their income above the basic rate
   limit, with pension relief and Gift Aid (which extends the limits, ITA
   2007 s. 414(2)(b)) in play.
"""

import numpy as np
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

PROPERTY_SETTINGS = settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
# 2019 has a 1,250 transferable amount, 2026 current rates and the 10.75%
# dividend ordinary rate, 2027 the property and savings rates (Finance Act
# 2026).
YEARS = [2019, 2026, 2027]
REGIONS = ["LONDON", "NORTH_EAST", "WALES", "SCOTLAND"]
INCOMES = {
    "employment_income": 60_000,
    "self_employment_income": 20_000,
    "private_pension_income": 20_000,
    "state_pension": 15_000,
    "savings_interest_income": 20_000,
    "dividend_income": 15_000,
    "property_income": 10_000,
}
# Residential finance costs give the landlord a Step 6 reduction of their own
# (ITTOIA 2005 s. 274AA), deducted before the Marriage Allowance reduction.
# They also make the property allowance a choice that income tax weighs in
# branches of its own, which is slow, so about a quarter of the generated
# populations have them, and LANDLORD_COUPLE is always tried.
FINANCE_COSTS = 10_000
# A landlord whose finance-cost reduction clears their tax, married to a
# low earner who would pay 138 to elect: electing saves the landlord nothing.
LANDLORD_COUPLE = [
    dict(
        adults=[
            dict(age=40, property_income=20_000.0, property_finance_costs=15_000.0),
            dict(age=38, employment_income=12_000.0),
        ],
        married=True,
        children=[],
        region="LONDON",
        married_couples_allowance=0.0,
    )
]
# A low earner whose small lettings are within the property allowance. Full
# relief and an election save the couple 114; electing out of the allowance
# for the finance-cost reduction saves the low earner 132 but stops the
# election, costing the couple 120 more. The route must be weighed on the
# couple's tax (independent review of #1963, 12 Oct 2026).
SMALL_LETTINGS_COUPLE = [
    dict(
        adults=[
            dict(age=40, employment_income=30_000.0),
            dict(
                age=38,
                employment_income=12_000.0,
                property_income=800.0,
                property_rental_income=800.0,
                property_finance_costs=200.0,
            ),
        ],
        married=True,
        children=[],
        region="LONDON",
        married_couples_allowance=0.0,
    )
]
ELECTION = "makes_marriage_allowance_election"
VARIABLES = [
    ELECTION,
    "is_marriage_allowance_spouse",
    "marriage_allowance_transferable_amount",
    "marriage_allowance_relinquished",
    "marriage_allowance",
    "marriage_allowance_appropriate_percentage",
    "marriage_allowance_tax_reduction",
    "marriage_allowance_tax_reduction_limit",
    "meets_marriage_allowance_income_conditions",
    "personal_allowance",
    "income_tax",
]
TOLERANCE = 0.01


def amounts(cap):
    # Many incomes are zero, so the allowances and bands are often unused.
    return st.one_of(st.just(0.0), st.floats(0, cap))


@st.composite
def adults(draw, finance_costs=False):
    age = draw(st.integers(18, 100))
    adult = dict(age=age)
    for variable, cap in INCOMES.items():
        if variable == "state_pension" and age < 67:
            continue
        adult[variable] = draw(amounts(cap))
    if finance_costs:
        adult["property_finance_costs"] = draw(amounts(FINANCE_COSTS))
    return adult


@st.composite
def families(draw, finance_costs=False):
    return dict(
        adults=[
            draw(adults(finance_costs))
            for _ in range(draw(st.sampled_from([1, 2, 2, 2])))
        ],
        married=draw(st.sampled_from([True, True, True, False])),
        children=[draw(st.integers(0, 15)) for _ in range(draw(st.integers(0, 2)))],
        region=draw(st.sampled_from(REGIONS)),
        # s. 55B(2)(d): now and then the first adult claims married couple's
        # allowance.
        married_couples_allowance=draw(st.sampled_from([0.0] * 9 + [11_270.0])),
    )


def situation(units, year, election=None, bump=None):
    """One simulation holding every family.

    ``election``, one value per person in order, fixes who elects.
    ``bump`` is (family index, adult index, variable, amount) to add.
    """
    people, benunits, households = {}, {}, {}
    for i, unit in enumerate(units):
        names = []
        for j, adult in enumerate(unit["adults"]):
            person = {"state_pension": {year: 0.0}}
            for variable, value in adult.items():
                person[variable] = {year: value}
            if j == 0:
                person["married_couples_allowance"] = {
                    year: unit["married_couples_allowance"]
                }
            if bump is not None and bump[:2] == (i, j):
                person[bump[2]] = {year: adult.get(bump[2], 0.0) + bump[3]}
            people[f"p{i}_{j}"] = person
            names.append(f"p{i}_{j}")
        for k, age in enumerate(unit["children"]):
            people[f"c{i}_{k}"] = {"age": {year: age}}
            names.append(f"c{i}_{k}")
        benunits[f"b{i}"] = {
            "members": names,
            "is_married": {year: unit["married"] and len(unit["adults"]) == 2},
        }
        households[f"h{i}"] = {"members": names, "region": {year: unit["region"]}}
    if election is not None:
        for person, elects in zip(people.values(), election):
            person[ELECTION] = {year: bool(elects)}
    return {"people": people, "benunits": benunits, "households": households}


def calculate(units, year, **kwargs):
    sim = Simulation(situation=situation(units, year, **kwargs))
    values = {v: np.asarray(sim.calculate(v, year)) for v in VARIABLES}
    values["benunit"] = np.asarray(sim.populations["benunit"].members_entity_id)
    return values


def per_person(units, adult_value, child_value=0.0):
    """One value per person in input order: adults, then children."""
    return np.array(
        [
            value
            for unit in units
            for value in [adult_value(unit, j) for j in range(len(unit["adults"]))]
            + [child_value] * len(unit["children"])
        ]
    )


def couple_total(values, variable):
    """Each person's couple total of ``variable``."""
    total = np.bincount(values["benunit"], weights=values[variable])
    return total[values["benunit"]]


def spouses_by_order(values):
    """Masks for the first and second spouse of each couple, in input order."""
    spouse = values["is_marriage_allowance_spouse"]
    first = np.zeros_like(spouse)
    second = np.zeros_like(spouse)
    seen = set()
    for i, (is_spouse, unit) in enumerate(zip(spouse, values["benunit"])):
        if not is_spouse:
            continue
        if unit in seen:
            second[i] = True
        else:
            first[i] = True
            seen.add(unit)
    return first, second


@st.composite
def populations(draw):
    finance_costs = draw(st.sampled_from([False, False, False, True]))
    return draw(st.lists(families(finance_costs), min_size=1, max_size=8))


couple_populations = populations()


@PROPERTY_SETTINGS
@given(units=couple_populations, year=st.sampled_from(YEARS))
@example(units=LANDLORD_COUPLE, year=2026)
@example(units=SMALL_LETTINGS_COUPLE, year=2026)
def test_election_never_raises_the_couples_tax(units, year):
    model = calculate(units, year)
    none = calculate(units, year, election=np.zeros_like(model[ELECTION]))
    model_tax = couple_total(model, "income_tax")
    none_tax = couple_total(none, "income_tax")
    assert np.all(model_tax <= none_tax + TOLERANCE), units
    # A couple that elects saves at least a penny.
    elects = couple_total(model, ELECTION) > 0
    assert np.all(model_tax[elects] <= none_tax[elects] - TOLERANCE + 1e-6), units


@PROPERTY_SETTINGS
@given(units=couple_populations, year=st.sampled_from(YEARS))
@example(units=LANDLORD_COUPLE, year=2026)
@example(units=SMALL_LETTINGS_COUPLE, year=2026)
def test_election_is_the_best_allowed_choice(units, year):
    model = calculate(units, year)
    none = calculate(units, year, election=np.zeros_like(model[ELECTION]))
    first, second = spouses_by_order(model)
    options = [none]
    allowed = [np.ones_like(first)]
    claims_mca = per_person(
        units, lambda unit, j: float(j == 0 and unit["married_couples_allowance"] > 0)
    )
    no_mca = couple_total(dict(benunit=model["benunit"], mca=claims_mca), "mca") == 0
    for elector in [first, second]:
        run = calculate(units, year, election=elector)
        gainer = model["is_marriage_allowance_spouse"] & ~elector
        # s. 55C(1)(b), (c): the elector has an allowance and, with it cut,
        # pays only basic rates; s. 55B(2)(b): so does the gaining partner;
        # s. 55B(2)(d): no married couple's allowance.
        conditions = (
            elector
            & (none["personal_allowance"] > 0)
            & run["meets_marriage_allowance_income_conditions"]
        ) | (gainer & none["meets_marriage_allowance_income_conditions"])
        couple_ok = (
            couple_total(dict(benunit=model["benunit"], ok=conditions), "ok") == 2
        ) & no_mca
        options.append(run)
        allowed.append(couple_ok)
    best = couple_total(none, "income_tax")
    for run, ok in zip(options[1:], allowed[1:]):
        best = np.where(ok, np.minimum(best, couple_total(run, "income_tax")), best)
    np.testing.assert_allclose(
        couple_total(model, "income_tax"), best, atol=TOLERANCE, err_msg=str(units)
    )


@st.composite
def bumped(draw):
    units = draw(populations())
    i = draw(st.integers(0, len(units) - 1))
    j = draw(st.integers(0, len(units[i]["adults"]) - 1))
    variables = [
        v for v in INCOMES if v != "state_pension" or units[i]["adults"][j]["age"] >= 67
    ]
    return units, (i, j, draw(st.sampled_from(variables)), draw(st.floats(1, 30_000)))


@PROPERTY_SETTINGS
@given(case=bumped(), year=st.sampled_from(YEARS))
def test_gaining_partner_is_independent_of_the_electors_income(case, year):
    units, (i, j, variable, amount) = case
    base = calculate(units, year)
    # The bumped adult elects wherever they are a spouse.
    person_index = (
        sum(len(unit["adults"]) + len(unit["children"]) for unit in units[:i]) + j
    )
    election = np.zeros_like(base[ELECTION])
    election[person_index] = base["is_marriage_allowance_spouse"][person_index]
    low = calculate(units, year, election=election)
    high = calculate(units, year, election=election, bump=(i, j, variable, amount))
    others = np.arange(len(election)) != person_index
    for variable_name in [
        "marriage_allowance",
        "marriage_allowance_tax_reduction",
        "personal_allowance",
        "income_tax",
    ]:
        np.testing.assert_allclose(
            high[variable_name][others],
            low[variable_name][others],
            atol=TOLERANCE,
            err_msg=f"{variable_name} {case}",
        )
    # s. 55B(6): the elector's allowance falls by the transferable amount.
    none = calculate(units, year, election=np.zeros_like(election))
    for run in [low]:
        np.testing.assert_allclose(
            run["personal_allowance"],
            np.maximum(
                0,
                none["personal_allowance"]
                - election * run["marriage_allowance_transferable_amount"],
            ),
            atol=TOLERANCE,
            err_msg=str(case),
        )


@PROPERTY_SETTINGS
@given(units=couple_populations, year=st.sampled_from(YEARS))
def test_marriage_allowance_accounting(units, year):
    model = calculate(units, year)
    none = calculate(units, year, election=np.zeros_like(model[ELECTION]))
    spouse = model["is_marriage_allowance_spouse"]
    elects = model[ELECTION]
    # Only spouses elect, at most one per couple.
    assert not np.any(elects & ~spouse), units
    assert np.all(couple_total(model, ELECTION) <= 1), units
    # What one spouse gives up the other receives.
    np.testing.assert_allclose(
        couple_total(model, "marriage_allowance"),
        couple_total(model, "marriage_allowance_relinquished"),
        atol=TOLERANCE,
    )
    transferable = model["marriage_allowance_transferable_amount"]
    received = model["marriage_allowance"]
    assert np.all(np.isclose(received, 0) | np.isclose(received, transferable)), units
    # The reduction is bounded by s. 55B(1), (3) and s. 29(2).
    reduction = model["marriage_allowance_tax_reduction"]
    rate = model["marriage_allowance_appropriate_percentage"]
    assert np.all(reduction <= rate * received + TOLERANCE), units
    assert np.all(
        reduction <= model["marriage_allowance_tax_reduction_limit"] + TOLERANCE
    ), units
    # The gaining partner's tax falls by exactly the reduction.
    gainer = received > 0
    np.testing.assert_allclose(
        model["income_tax"][gainer],
        none["income_tax"][gainer] - reduction[gainer],
        atol=TOLERANCE,
        err_msg=str(units),
    )
    # The elector pays at least as much as without the election.
    assert np.all(
        model["income_tax"][elects] >= none["income_tax"][elects] - TOLERANCE
    ), units


@PROPERTY_SETTINGS
@given(case=bumped(), year=st.sampled_from(YEARS))
def test_couples_tax_never_falls_with_more_income(case, year):
    units, bump = case
    low = calculate(units, year)
    high = calculate(units, year, bump=bump)
    assert np.all(
        couple_total(high, "income_tax") >= couple_total(low, "income_tax") - TOLERANCE
    ), (bump, units)


@PROPERTY_SETTINGS
@given(units=couple_populations, year=st.sampled_from(YEARS))
def test_only_married_couples_transfer(units, year):
    model = calculate(units, year)
    outside = ~model["is_marriage_allowance_spouse"]
    for variable in [
        ELECTION,
        "marriage_allowance",
        "marriage_allowance_relinquished",
        "marriage_allowance_tax_reduction",
    ]:
        assert np.all(model[variable][outside] == 0), (variable, units)
    married_pairs = {
        i
        for i, unit in enumerate(units)
        if unit["married"] and len(unit["adults"]) == 2
    }
    spouse_units = set(model["benunit"][model["is_marriage_allowance_spouse"]])
    assert spouse_units == married_pairs, units


# Incomes the rate test and the band variables both see. Dividends (tested as
# if the dividend nil rate were omitted, s. 55B(2)(ba)) and property income
# (banded inside property_income_tax) have no band variables to compare with.
BANDED_INCOMES = {
    "employment_income": 160_000,
    "private_pension_income": 30_000,
    "savings_interest_income": 20_000,
    # Net pay arrangement and relief at source (FA 2004 ss. 188-192).
    "employee_pension_contributions": 20_000,
    "personal_pension_contributions": 10_000,
    "gift_aid": 10_000,
}
ABOVE_BASIC_RATE = [
    "higher_rate_earned_income",
    "add_rate_earned_income",
    "higher_rate_savings_income",
    "add_rate_savings_income",
]
# At the basic rate limit after pension relief, and 1 above it.
PENSION_SAVERS = [
    dict(employment_income=55_270.0, employee_pension_contributions=5_000.0),
    dict(employment_income=55_271.0, employee_pension_contributions=5_000.0),
]


@st.composite
def taxpayers(draw):
    return {variable: draw(amounts(cap)) for variable, cap in BANDED_INCOMES.items()}


@PROPERTY_SETTINGS
@given(
    people=st.lists(taxpayers(), min_size=1, max_size=20), year=st.sampled_from(YEARS)
)
@example(people=PENSION_SAVERS, year=2026)
def test_income_conditions_match_the_tax_bands(people, year):
    # The rate test (s. 55B(2)(b), s. 55C(1)(c)) must use the income the tax
    # bands use (net income less allowances, so pension relief once) and the
    # same Gift Aid-extended limits.
    situation = {"people": {}, "benunits": {}, "households": {}}
    for i, incomes in enumerate(people):
        person = {variable: {year: value} for variable, value in incomes.items()}
        situation["people"][f"p{i}"] = {"age": {year: 40}, **person}
        situation["benunits"][f"b{i}"] = {"members": [f"p{i}"]}
        situation["households"][f"h{i}"] = {
            "members": [f"p{i}"],
            "region": {year: "LONDON"},
        }
    sim = Simulation(situation=situation)
    above_basic = sum(np.asarray(sim.calculate(v, year)) for v in ABOVE_BASIC_RATE)
    meets = np.asarray(
        sim.calculate("meets_marriage_allowance_income_conditions", year)
    )
    np.testing.assert_array_equal(meets, above_basic <= 0, err_msg=str(people))


def test_2015_transferable_amount_is_fixed_whatever_the_allowance():
    # ITA 2007 s. 55B(4)(a) fixes 2015-16 at 1,060; only later years take 10%
    # of the s. 35(1) allowance. With the 2015 allowance raised to 15,000 the
    # transfer is still 1,060: the transferor's allowance falls to 13,940 and
    # the recipient on 30,000 pays (30,000 - 15,000) x 20% - 212 = 2,788.
    year = 2015
    situation = {
        "people": {
            "recipient": {"age": {year: 40}, "employment_income": {year: 30_000}},
            "transferor": {"age": {year: 38}},
        },
        "benunits": {
            "couple": {
                "members": ["recipient", "transferor"],
                "is_married": {year: True},
            }
        },
        "households": {"home": {"members": ["recipient", "transferor"]}},
    }
    sim = Simulation(
        situation=situation,
        reform={
            "gov.hmrc.income_tax.allowances.personal_allowance.amount": {
                "2015-01-01.2015-12-31": 15_000
            }
        },
    )
    np.testing.assert_allclose(
        sim.calculate("marriage_allowance_transferable_amount", year), [1_060, 1_060]
    )
    np.testing.assert_allclose(
        sim.calculate("personal_allowance", year), [15_000, 13_940]
    )
    np.testing.assert_allclose(sim.calculate("income_tax", year), [2_788, 0])
