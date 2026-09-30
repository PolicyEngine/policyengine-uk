"""Property-based tests for the Marriage Allowance (ITA 2007 ss. 55A-55E).

An election by one spouse or civil partner cuts their own personal allowance
by the transferable amount (s. 55B(6)) and gives the other a Step 6 tax
reduction of the appropriate percentage of it, capped at their Step 5 tax
(s. 55A(2), s. 55B(1), (3), s. 29(2)). The couple elects only when the
conditions allow it and it lowers their combined income tax.

Invariants, for any generated population of couples with every kind of
taxable income, in England, Wales or Scotland:

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
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
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
def adults(draw):
    age = draw(st.integers(18, 100))
    adult = dict(age=age)
    for variable, cap in INCOMES.items():
        if variable == "state_pension" and age < 67:
            continue
        adult[variable] = draw(amounts(cap))
    return adult


@st.composite
def families(draw):
    return dict(
        adults=[draw(adults()) for _ in range(draw(st.sampled_from([1, 2, 2, 2])))],
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


couple_populations = st.lists(families(), min_size=1, max_size=8)


@PROPERTY_SETTINGS
@given(units=couple_populations, year=st.sampled_from(YEARS))
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
    units = draw(st.lists(families(), min_size=1, max_size=8))
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
