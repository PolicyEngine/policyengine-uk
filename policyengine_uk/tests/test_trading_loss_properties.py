"""Property-based tests for the trading loss input (trading_loss).

A trading loss is entered as a positive amount, separate from the profits in
self_employment_income, and each programme reads it by its own rule.
Invariants, for any people and incomes:

1. Relief definition (ITA 2007 s.64, s.24A): trade loss relief against
   general income equals min(loss, max(£50,000, 25% of adjusted total
   income), net income). Net income is the adjusted net income of the same
   person without the loss (a separate simulation); adjusted total income is
   that less the pension contributions given relief (own contributions up to
   the greater of £3,600 and pay plus profits, none from age 75).
2. Differential: a person's Income Tax with a loss equals the Income Tax of
   the same person without the loss and with their income cut by the relief,
   taken from non-savings income first, then savings, then dividends: the
   model's fixed allowance order (s.25(2) asks for the order giving the
   greatest reduction; #2106).
3. Income Tax never rises with the loss and falls by at most the relief (for
   people without savings income: the personal savings allowance steps up by
   £500 when someone stops being a higher-rate taxpayer, so with savings
   income a small relief can save more than itself).
4. Means tests never set the loss against employed earnings or other
   income: with Income Tax and NI held at the values the loss gives, every
   means-tested benefit and means-test income is what it is without the loss,
   except that UC sets it against the person's other trades' profits (UC Regs
   2013 reg 57(2)), so UC, its benefit cap earnings test and the capped
   award equal the same family with those profits cut by the loss. (The model's means tests deduct the year's Income Tax liability,
   so otherwise the loss reaches them only through that tax.)
5. Tax credits (SI 2002/2006 reg 3(1) Step 4): the claimants' losses (not a
   child's) come off their applicable income, never below zero, and the award
   never falls.
6. Household income: market income falls by exactly the household's losses,
   and HBAI net income moves only through the loss itself, taxes and
   means-tested or passported benefits; every other component is unchanged.
7. Class 4 (SSCBA 1992 Sch 2 para 3): Class 4 profits are self-employment
   profits less losses brought forward (for both taxes and for Class 4 only)
   and the year's relief, never below zero, so Class 4 never rises with the
   loss and someone with no profits pays none whatever their loss.
8. The s.24A cap starts in 2013-14.

Comparisons allow float32 rounding: the model stores values as float32.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import CountryTaxBenefitSystem, Simulation
from policyengine_uk.variables.household.income.hbai_household_net_income import (
    HBAI_HOUSEHOLD_NET_INCOME_ADDS,
    HBAI_HOUSEHOLD_NET_INCOME_SUBTRACTS,
)

YEAR = 2026
PROPERTY_SETTINGS = settings(
    max_examples=3,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
REGIONS = ["LONDON", "NORTH_EAST", "SCOTLAND", "WALES"]
# Means tests other than UC, compared with UC held (CTR counts UC as income).
MEANS_TESTED = [
    "housing_benefit",
    "council_tax_reduction",
    "pension_credit",
    "income_support",
    "jsa_income",
    "esa_income",
    "housing_benefit_applicable_income",
    "income_support_applicable_income",
    "council_tax_reduction_applicable_income",
    "pension_credit_income",
]
UC_TESTS = [
    "uc_earned_income",
    "universal_credit_pre_benefit_cap",
    "is_benefit_cap_exempt_earnings",
    "universal_credit",
]
# HBAI components the loss may move: the loss itself, taxes, and benefits
# that are means-tested or passported from a means-tested benefit.
HBAI_CHANNELS = {
    "trading_loss",
    "income_tax",
    "national_insurance",
    "student_loan_repayments",
    "universal_credit",
    "housing_benefit",
    "council_tax_benefit",
    "pension_credit",
    "income_support",
    "jsa_income",
    "esa_income",
    "working_tax_credit",
    "child_tax_credit",
    "tax_free_childcare",
    "free_school_meals",
    "free_school_fruit_veg",
    "free_school_milk",
    "healthy_start_vouchers",
    "scottish_child_payment",
    "cost_of_living_support_payment",
}


def money(high):
    return st.one_of(
        st.just(0.0),
        st.floats(1, high, allow_nan=False, allow_infinity=False),
    )


def tolerance(*amounts):
    # float32 has a 24-bit significand: a few ulps of the largest amount
    # involved, plus a penny.
    return 0.01 + 4e-7 * max([abs(float(a)) for a in amounts] + [1])


@st.composite
def taxpayers(draw):
    """One working-age person with income of every taxed kind and a loss."""
    return {
        "age": draw(st.integers(18, 80)),
        "employment_income": draw(money(250_000)),
        "private_pension_income": draw(money(60_000)),
        "savings_interest_income": draw(money(40_000)),
        "dividend_income": draw(money(150_000)),
        "property_income": draw(money(40_000)),
        "self_employment_income": draw(money(80_000)),
        "personal_pension_contributions": draw(money(30_000)),
        "trading_loss": draw(money(300_000)),
        "state_pension": 0.0,
    }


def single_people(people, regions):
    situation = {"people": {}, "benunits": {}, "households": {}}
    for i, (inputs, region) in enumerate(zip(people, regions)):
        name = f"p{i}"
        situation["people"][name] = {k: {YEAR: v} for k, v in inputs.items()}
        situation["benunits"][f"b{i}"] = {"members": [name]}
        situation["households"][f"h{i}"] = {
            "members": [name],
            "region": {YEAR: region},
        }
    return situation


def calculate(situation, variables, year=YEAR):
    sim = Simulation(situation=situation)
    return {v: np.asarray(sim.calculate(v, year), dtype=float) for v in variables}


@PROPERTY_SETTINGS
@given(
    st.lists(taxpayers(), min_size=8, max_size=16),
    st.lists(st.sampled_from(REGIONS), min_size=16, max_size=16),
)
def test_relief_is_the_loss_within_net_income_and_the_cap(people, regions):
    without = [{**p, "trading_loss": 0.0} for p in people]
    a = calculate(
        single_people(people, regions),
        ["trade_loss_relief_against_general_income", "adjusted_net_income"],
    )
    b = calculate(
        single_people(without, regions),
        [
            "adjusted_net_income",
            "taxable_employment_income",
            "taxable_self_employment_income",
        ],
    )
    for i, person in enumerate(people):
        # Relevant UK earnings (FA 2004 s.189(2)): taxable pay and profits.
        earnings = (
            b["taxable_employment_income"][i] + b["taxable_self_employment_income"][i]
        )
        relieved = (person["age"] < 75) * min(
            person["personal_pension_contributions"], max(3_600.0, earnings)
        )
        ati = max(0.0, b["adjusted_net_income"][i] - relieved)
        cap = max(50_000.0, 0.25 * ati)
        expected = min(person["trading_loss"], cap, b["adjusted_net_income"][i])
        relief = a["trade_loss_relief_against_general_income"][i]
        assert abs(relief - expected) <= tolerance(expected, ati), (person, relief)
        # Net income falls by exactly the relief.
        assert abs(
            b["adjusted_net_income"][i] - relief - a["adjusted_net_income"][i]
        ) <= tolerance(b["adjusted_net_income"][i]), person


@st.composite
def portfolio_holders(draw):
    """Pay, pension, savings and dividends only, so the reduced-income twin
    differs from the person only in those four amounts."""
    return {
        "age": draw(st.integers(18, 64)),
        "employment_income": draw(money(250_000)),
        "private_pension_income": draw(money(60_000)),
        "savings_interest_income": draw(money(40_000)),
        "dividend_income": draw(money(150_000)),
        "trading_loss": draw(money(300_000)),
        "state_pension": 0.0,
    }


def reduced(person):
    """The person's income cut by the relief, in the s.25 order the model
    uses, computed outside the model."""
    pay = person["employment_income"]
    pension = person["private_pension_income"]
    savings = person["savings_interest_income"]
    dividends = person["dividend_income"]
    total = pay + pension + savings + dividends
    relief = min(person["trading_loss"], max(50_000.0, 0.25 * total), total)
    left = relief
    out = {}
    for name, amount in [
        ("employment_income", pay),
        ("private_pension_income", pension),
        ("savings_interest_income", savings),
        ("dividend_income", dividends),
    ]:
        cut = min(left, amount)
        out[name] = amount - cut
        left -= cut
    return {**person, **out, "trading_loss": 0.0}, relief


@PROPERTY_SETTINGS
@given(
    st.lists(portfolio_holders(), min_size=8, max_size=16),
    st.lists(st.sampled_from(REGIONS), min_size=16, max_size=16),
)
def test_relief_taxes_like_income_cut_in_section_25_order(people, regions):
    twins = [reduced(p)[0] for p in people]
    variables = ["income_tax", "trade_loss_relief_against_general_income"]
    a = calculate(single_people(people, regions), variables)
    b = calculate(single_people(twins, regions), ["income_tax"])
    for i, person in enumerate(people):
        _, relief = reduced(person)
        assert abs(a["trade_loss_relief_against_general_income"][i] - relief) <= (
            tolerance(relief)
        ), person
        assert abs(a["income_tax"][i] - b["income_tax"][i]) <= 0.5 + tolerance(
            a["income_tax"][i], person["employment_income"]
        ), (person, a["income_tax"][i], b["income_tax"][i])


@PROPERTY_SETTINGS
@given(
    st.lists(taxpayers(), min_size=8, max_size=16),
    st.lists(st.sampled_from(REGIONS), min_size=16, max_size=16),
    st.floats(0, 1),
)
def test_income_tax_falls_with_the_loss_by_at_most_the_relief(people, regions, share):
    smaller = [{**p, "trading_loss": p["trading_loss"] * share} for p in people]
    without = [{**p, "trading_loss": 0.0} for p in people]
    variables = ["income_tax", "trade_loss_relief_against_general_income"]
    a = calculate(single_people(people, regions), variables)
    s = calculate(single_people(smaller, regions), variables)
    b = calculate(single_people(without, regions), variables)
    for i, person in enumerate(people):
        tol = tolerance(b["income_tax"][i], person["employment_income"])
        assert a["income_tax"][i] <= s["income_tax"][i] + tol, person
        assert s["income_tax"][i] <= b["income_tax"][i] + tol, person
        if person["savings_interest_income"] == 0:
            saved = b["income_tax"][i] - a["income_tax"][i]
            relief = a["trade_loss_relief_against_general_income"][i]
            assert saved <= relief + tol, (person, saved, relief)


@st.composite
def families(draw):
    """A benefit unit with a head, maybe a partner and children, rent and
    council tax, where the adults may have a trading loss."""
    head_age = draw(st.integers(18, 80))
    adults = [head_age]
    if draw(st.booleans()):
        adults.append(draw(st.integers(18, 80)))
    people = [
        {
            "age": age,
            "employment_income": draw(money(60_000)),
            "self_employment_income": draw(money(30_000)),
            "private_pension_income": draw(money(20_000)),
            "savings_interest_income": draw(money(5_000)),
            "trading_loss": draw(money(40_000)),
            "hours_worked": draw(st.sampled_from([0.0, 16.0, 35.0])),
        }
        for age in adults
    ]
    for _ in range(draw(st.integers(0, 3))):
        # A child's own trading loss is never the claimants'.
        people.append(
            {"age": draw(st.integers(0, 15)), "trading_loss": draw(money(5_000))}
        )
    household = {
        "rent": draw(money(15_000)),
        "council_tax": draw(money(3_000)),
        "tenure_type": draw(st.sampled_from(["RENT_PRIVATELY", "RENT_FROM_COUNCIL"])),
        "region": draw(st.sampled_from(REGIONS)),
    }
    return people, household


def family_situation(units, overrides=None, benunit_overrides=None):
    situation = {"people": {}, "benunits": {}, "households": {}}
    for i, (people, household) in enumerate(units):
        names = []
        for j, inputs in enumerate(people):
            name = f"p{i}_{j}"
            values = dict(inputs)
            if overrides is not None:
                values.update(overrides.get(name, {}))
            situation["people"][name] = {k: {YEAR: v} for k, v in values.items()}
            names.append(name)
        situation["benunits"][f"b{i}"] = {
            "members": names,
            **{
                k: {YEAR: v}
                for k, v in (benunit_overrides or {}).get(f"b{i}", {}).items()
            },
        }
        situation["households"][f"h{i}"] = {
            "members": names,
            **{k: {YEAR: v} for k, v in household.items()},
        }
    return situation


@PROPERTY_SETTINGS
@given(st.lists(families(), min_size=4, max_size=10))
def test_means_tests_see_the_loss_only_through_tax(units):
    with_loss = Simulation(situation=family_situation(units))

    def values(sim, variable):
        return np.asarray(sim.calculate(variable, YEAR), dtype=float)

    names = with_loss.populations["person"].ids
    benunits = with_loss.populations["benunit"].ids
    tax = {v: values(with_loss, v) for v in ["income_tax", "national_insurance"]}
    loss = values(with_loss, "trading_loss")
    profits = values(with_loss, "self_employment_income")
    mif = np.asarray(with_loss.calculate("uc_mif_applies", YEAR))
    uc = values(with_loss, "universal_credit")
    hb = values(with_loss, "housing_benefit")

    def held(k, **extra):
        return {
            "trading_loss": 0.0,
            "income_tax": float(tax["income_tax"][k]),
            "national_insurance": float(tax["national_insurance"][k]),
            **extra,
        }

    # Every means test but UC: the loss reaches them only through the tax.
    no_loss = Simulation(
        situation=family_situation(
            units,
            {name: held(k) for k, name in enumerate(names)},
            {b: {"universal_credit": float(uc[k])} for k, b in enumerate(benunits)},
        )
    )
    for variable in MEANS_TESTED:
        a, b = values(with_loss, variable), values(no_loss, variable)
        assert np.allclose(a, b, atol=0.5), (variable, a, b, units)
    # UC: as if the loss had cut the person's other trades' profits.
    netted = Simulation(
        situation=family_situation(
            units,
            {
                name: held(
                    k,
                    self_employment_income=float(profits[k] - min(loss[k], profits[k])),
                    uc_mif_applies=bool(mif[k]),
                )
                for k, name in enumerate(names)
            },
            # The cap counts Housing Benefit, which reads profits before any
            # loss: hold it at the with-loss value.
            {b: {"housing_benefit": float(hb[k])} for k, b in enumerate(benunits)},
        )
    )
    for variable in UC_TESTS:
        a, b = values(with_loss, variable), values(netted, variable)
        assert np.allclose(a, b, atol=0.5), (variable, a, b, units)


@PROPERTY_SETTINGS
@given(st.lists(families(), min_size=4, max_size=10))
def test_tax_credit_income_falls_by_the_claimants_losses(units):
    year = 2024
    without = [
        ([{**p, "trading_loss": 0.0} if "trading_loss" in p else p for p in people], h)
        for people, h in units
    ]

    def run(us):
        situation = family_situation(us)
        for person in situation["people"].values():
            for key, value in list(person.items()):
                person[key] = {year: value[YEAR]}
        for household in situation["households"].values():
            for key, value in list(household.items()):
                if key != "members":
                    household[key] = {year: value[YEAR]}
        sim = Simulation(situation=situation)
        return {
            v: np.asarray(sim.calculate(v, year), dtype=float)
            for v in ["tax_credits_applicable_income", "tax_credits"]
        }, sim

    a, sim = run(units)
    b, _ = run(without)
    members = sim.calculate("is_claimant_or_partner", year)
    loss = np.asarray(sim.calculate("trading_loss", year), dtype=float)
    benunit_loss = sim.map_result(loss * members, "person", "benunit")
    expected = np.maximum(0, b["tax_credits_applicable_income"] - benunit_loss)
    # On income-related IS, ESA or JSA the applicable income is nil anyway.
    on_exempt = b["tax_credits_applicable_income"] == 0
    assert np.allclose(
        a["tax_credits_applicable_income"], np.where(on_exempt, 0, expected), atol=0.5
    ), (a, expected, units)
    assert np.all(a["tax_credits"] >= b["tax_credits"] - 0.5), units


@PROPERTY_SETTINGS
@given(st.lists(families(), min_size=4, max_size=10))
def test_household_income_moves_only_through_its_channels(units):
    without = [
        ([{**p, "trading_loss": 0.0} if "trading_loss" in p else p for p in people], h)
        for people, h in units
    ]
    components = sorted(
        set(HBAI_HOUSEHOLD_NET_INCOME_ADDS + HBAI_HOUSEHOLD_NET_INCOME_SUBTRACTS)
    )
    variables = components + ["household_market_income", "hbai_household_net_income"]
    a_sim = Simulation(situation=family_situation(units))
    b_sim = Simulation(situation=family_situation(without))

    def household_values(sim, variable):
        values = np.asarray(sim.calculate(variable, YEAR), dtype=float)
        entity = sim.tax_benefit_system.get_variable(variable).entity.key
        if entity == "household":
            return values
        return sim.map_result(values, entity, "household")

    a = {v: household_values(a_sim, v) for v in variables}
    b = {v: household_values(b_sim, v) for v in variables}
    losses = a["trading_loss"]
    assert np.allclose(
        a["household_market_income"], b["household_market_income"] - losses, atol=0.5
    )
    for variable in components:
        if variable not in HBAI_CHANNELS:
            assert np.allclose(a[variable], b[variable], atol=0.5), variable
    channels = sum(
        (a[v] - b[v]) * (1 if v in HBAI_HOUSEHOLD_NET_INCOME_ADDS else -1)
        for v in components
        if v in HBAI_CHANNELS
    )
    assert np.allclose(
        a["hbai_household_net_income"] - b["hbai_household_net_income"],
        channels,
        atol=1,
    )


@PROPERTY_SETTINGS
@given(
    st.lists(taxpayers(), min_size=8, max_size=16),
    st.lists(st.sampled_from(REGIONS), min_size=16, max_size=16),
    st.lists(money(20_000), min_size=16, max_size=16),
)
def test_class_4_profits_net_of_the_relief(people, regions, brought_forward):
    people = [{**p, "loss_relief": b} for p, b in zip(people, brought_forward)]
    without = [{**p, "trading_loss": 0.0} for p in people]
    variables = [
        "ni_class_4_profits",
        "ni_class_4",
        "trade_loss_relief_against_general_income",
    ]
    a = calculate(single_people(people, regions), variables)
    b = calculate(single_people(without, regions), variables)
    for i, person in enumerate(people):
        expected = max(
            0.0,
            person["self_employment_income"]
            - person["loss_relief"]
            - a["trade_loss_relief_against_general_income"][i],
        )
        assert abs(a["ni_class_4_profits"][i] - expected) <= tolerance(
            person["self_employment_income"]
        ), person
        assert a["ni_class_4"][i] <= b["ni_class_4"][i] + tolerance(
            b["ni_class_4"][i]
        ), person
        if person["self_employment_income"] == 0:
            assert a["ni_class_4"][i] == 0, person


def test_cap_starts_in_2013_14():
    cap = CountryTaxBenefitSystem().parameters.gov.hmrc.income_tax.reliefs.cap
    assert cap.amount("2013-04-05") == np.inf
    assert cap.amount("2013-04-06") == 50_000
    assert cap.rate("2013-04-06") == 0.25
