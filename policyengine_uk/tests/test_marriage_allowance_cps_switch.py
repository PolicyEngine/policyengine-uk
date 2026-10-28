"""The CPS expanded Marriage Allowance switches on from its own parameters only.

``create_marriage_tax_reform`` adds the CPS expanded Marriage Allowance
(``gov.contrib.cps.marriage_tax_reforms.expanded_ma``) to a simulation whose
parameters switch it on. It used to switch on whenever the CPS rate differed
from the statutory Marriage Allowance rate
(``gov.hmrc.income_tax.allowances.marriage_allowance.max``), so changing the
statutory rate ran the reform (#2551). A statutory rate of 0 then kept a 10%
allowance for basic-rate couples and gave one to higher-rate couples. The
reform now switches on only when ``remove_income_condition`` is true or
``ma_rate`` differs from its unreformed value.

The switch runs when ``policyengine_uk.Simulation`` is built. YAML policy
tests build their simulations with core's ``SimulationBuilder``, which never
runs it, so these tests build Simulations, on each route a parameter change
can take.

Invariants, for every household and parameter value drawn:

1. The reform is on exactly when ``remove_income_condition`` is true or
   ``ma_rate`` differs from its default, whatever the statutory rate. At the
   statutory rate in force this is the old switch, so current law is unchanged.
2. With the statutory rate at 0 and the CPS parameters at their defaults, no
   one has a Marriage Allowance, and income tax is what it is at current law
   when no one claims the allowance.
3. With any statutory rate and the CPS parameters at their defaults, no one
   liable at the higher rate or above meets the income conditions or has the
   allowance, everyone else meets the conditions, and no one has more than the
   statutory share of the personal allowance, rounded up to the next £10.
4. The transferable amount never falls when the statutory rate rises, and the
   allowance is all of it or none. The allowance itself can fall: a couple
   stops electing once giving up the larger allowance costs the elector more
   than the partner gains (intended; ITA 2007 s. 55B(6)).
5. Switched on by its own parameters, the reform gives the expanded
   allowance as a Step 6 tax reduction (hand-computed values below).
"""

import functools
import math

import numpy as np
import pytest
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st
from policyengine_core import periods
from policyengine_core.reforms import Reform

import policyengine_uk.simulation as uk_simulation
from policyengine_uk import Simulation
from policyengine_uk.reforms.cps.marriage_tax_reforms import (
    create_marriage_tax_reform,
    expanded_ma_reform,
)
from policyengine_uk.utils.scenario import Scenario

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

# The 2025-26 tax year. The switch reads the parameters at the simulation's
# default input period, 2025, so every change below covers it.
YEAR = 2025
SPAN = "2025-01-01.2030-12-31"
STATUTORY_RATE = "gov.hmrc.income_tax.allowances.marriage_allowance.max"
EXPANDED_MA = "gov.contrib.cps.marriage_tax_reforms.expanded_ma"
CPS_RATE = f"{EXPANDED_MA}.ma_rate"
REMOVE_INCOME_CONDITION = f"{EXPANDED_MA}.remove_income_condition"
MAX_CHILD_AGE = f"{EXPANDED_MA}.max_child_age"
# Current law (marriage_allowance/max.yaml) and the CPS rate's default
# (expanded_ma/ma_rate.yaml) are both 10%.
CURRENT_STATUTORY_RATE = 0.1
DEFAULT_CPS_RATE = 0.1
# 2025-26 personal allowance, and the increment the allowance is rounded up to
# (marriage_allowance/rounding_increment.yaml).
PERSONAL_ALLOWANCE = 12_570
ROUNDING_INCREMENT = 10
# 2025-26 taxable income above which non-savings income is charged above the
# electing rates: the basic rate limit (ITA 2007 s. 10), and for a Scottish
# taxpayer the start of the Scottish higher rate, £43,662 of income less the
# personal allowance (Scottish Rate Resolution 2025).
BASIC_RATE_LIMIT = 37_700
SCOTTISH_HIGHER_RATE_START = 31_092
REFORM_VARIABLE = "meets_expanded_ma_conditions"  # Only the reform adds it.


def change(*pairs):
    return {path: {SPAN: value} for path, value in pairs}


def via_reform_dict(reform, situation):
    return Simulation(situation=situation, reform=reform)


def via_parameter_changes(reform, situation):
    return Simulation(situation=situation, scenario=Scenario(parameter_changes=reform))


def via_reform_from_dict(reform, situation):
    return Simulation(situation=situation, reform=Reform.from_dict(reform))


def via_scenario_before_data_load(reform, situation):
    scenario = Scenario.from_reform(reform)
    scenario.applied_before_data_load = True
    return Simulation(situation=situation, scenario=scenario)


ROUTES = {
    "reform_dict": via_reform_dict,
    "parameter_changes": via_parameter_changes,
    "reform_from_dict": via_reform_from_dict,
    "scenario_before_data_load": via_scenario_before_data_load,
}


def couples(*specs):
    """Married couples, each in its own benefit unit and household.

    Each spec is the earner's employment income and a child's age (None for
    no child). The partner has no income. People are listed couple by couple:
    earner, partner, then any child.
    """
    people, benunits, households = {}, {}, {}
    for i, (earnings, child_age) in enumerate(specs):
        members = [f"earner_{i}", f"partner_{i}"]
        people[members[0]] = {"age": {YEAR: 40}, "employment_income": {YEAR: earnings}}
        people[members[1]] = {"age": {YEAR: 40}, "employment_income": {YEAR: 0}}
        if child_age is not None:
            members.append(f"child_{i}")
            people[members[2]] = {"age": {YEAR: child_age}}
        benunits[f"benunit_{i}"] = {"members": members, "is_married": {YEAR: True}}
        households[f"household_{i}"] = {"members": members}
    return {"people": people, "benunits": benunits, "households": households}


# The issue's two couples, by hand from the 2025-26 parameters: a £12,570
# personal allowance, then 20% on the first £37,700 of taxable income and 40%
# above it. The earner of £30,000 pays (30,000 - 12,570) x 20% = 3,486. At
# current law the partner transfers 10% of the allowance, £1,257 rounded up to
# £1,260, worth 1,260 x 20% = 252: 3,234. The earner of £60,000 pays
# 37,700 x 20% + (60,000 - 12,570 - 37,700) x 40% = 7,540 + 3,892 = 11,432, and
# as a higher-rate taxpayer receives no allowance. At a 20% statutory rate the
# transfer is £2,514 rounded up to £2,520, worth 504: 3,486 - 504 = 2,982.
ISSUE_COUPLES = couples((30_000, None), (60_000, None))
EARNERS = [0, 2]


def outcome(simulation):
    allowance = simulation.calculate("marriage_allowance", YEAR)
    income_tax = simulation.calculate("income_tax", YEAR)
    return allowance.tolist(), income_tax[EARNERS].tolist()


def test_current_law_matches_the_hand_calculation():
    simulation = Simulation(situation=ISSUE_COUPLES)
    assert REFORM_VARIABLE not in simulation.tax_benefit_system.variables
    assert outcome(simulation) == ([1_260, 0, 0, 0], [3_234, 11_432])


@pytest.mark.parametrize("route", ROUTES)
def test_a_zero_statutory_rate_removes_the_allowance(route):
    simulation = ROUTES[route](change((STATUTORY_RATE, 0.0)), ISSUE_COUPLES)
    assert REFORM_VARIABLE not in simulation.tax_benefit_system.variables
    # The basic-rate earner pays 252 more; the higher-rate earner the same.
    assert outcome(simulation) == ([0, 0, 0, 0], [3_486, 11_432])


@pytest.mark.parametrize("route", ROUTES)
def test_a_higher_statutory_rate_raises_only_the_statutory_allowance(route):
    simulation = ROUTES[route](change((STATUTORY_RATE, 0.2)), ISSUE_COUPLES)
    assert REFORM_VARIABLE not in simulation.tax_benefit_system.variables
    assert outcome(simulation) == ([2_520, 0, 0, 0], [2_982, 11_432])


# Invariant 5, by hand. The allowance is a Step 6 tax reduction at the basic
# rate (ITA 2007 s. 55B(1), (3)), whatever the recipient's own marginal rate.
# Lifting the income condition lets the higher-rate earner gain: 11,432 -
# 1,260 x 20% = 11,180. A CPS rate alone keeps the income condition, so it
# raises the basic-rate couple's transfer to 2,520 (3,486 - 504 = 2,982) and
# leaves the higher-rate earner at 11,432.
OWN_SWITCHES = {
    "remove_income_condition": (
        change((REMOVE_INCOME_CONDITION, True)),
        ([1_260, 0, 1_260, 0], [3_234, 11_180]),
    ),
    "cps_rate": (
        change((CPS_RATE, 0.2)),
        ([2_520, 0, 0, 0], [2_982, 11_432]),
    ),
}


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("switch", OWN_SWITCHES)
def test_the_reform_still_switches_on_from_its_own_parameters(route, switch):
    reform, expected = OWN_SWITCHES[switch]
    simulation = ROUTES[route](reform, ISSUE_COUPLES)
    assert REFORM_VARIABLE in simulation.tax_benefit_system.variables
    assert outcome(simulation) == expected


def test_a_cps_rate_switches_the_reform_on_whatever_the_statutory_rate():
    # The old switch missed this: the two rates were equal. The income
    # condition stays, so only the basic-rate earner gains.
    reform = change((STATUTORY_RATE, 0.2), (CPS_RATE, 0.2))
    simulation = Simulation(situation=ISSUE_COUPLES, reform=reform)
    assert REFORM_VARIABLE in simulation.tax_benefit_system.variables
    assert outcome(simulation) == ([2_520, 0, 0, 0], [2_982, 11_432])


CHILD_CONDITION_COUPLES = couples(
    (30_000, None), (30_000, 3), (60_000, None), (60_000, 3)
)
CHILD_CONDITION_EARNERS = [0, 2, 5, 7]


@pytest.mark.parametrize(
    "statutory_rate, statutory_allowance", [(None, 1_260), (0.0, 0)]
)
def test_couples_outside_the_child_condition_keep_the_statutory_allowance(
    statutory_rate, statutory_allowance
):
    # With a child condition, only couples with a child under 5 get the CPS
    # rate. The rest keep the statutory allowance: the basic-rate earner
    # without a child gets the statutory rate. remove_income_condition is off,
    # so neither higher-rate earner gains, with a child or without.
    pairs = [(CPS_RATE, 0.2), (MAX_CHILD_AGE, 5)]
    if statutory_rate is not None:
        pairs.append((STATUTORY_RATE, statutory_rate))
    simulation = Simulation(situation=CHILD_CONDITION_COUPLES, reform=change(*pairs))
    allowance = simulation.calculate("marriage_allowance", YEAR)
    assert allowance[CHILD_CONDITION_EARNERS].tolist() == [
        statutory_allowance,
        2_520,
        0,
        0,
    ]
    others = np.delete(np.arange(len(allowance)), CHILD_CONDITION_EARNERS)
    assert (allowance[others] == 0).all()


# Invariant 1, on the switch itself.


@pytest.fixture(scope="module")
def parameters(cloned_uk_tax_benefit_system):
    return uk_simulation.CountryTaxBenefitSystem().parameters


def set_value(parameters, path, value):
    parameter = functools.reduce(getattr, path.split("."), parameters)
    parameter.update(period=periods.period("year:2000:60"), value=value)


def switched_on(parameters, year=YEAR):
    return create_marriage_tax_reform(parameters, periods.period(year)) is not None


@pytest.mark.parametrize("year", range(2016, 2036))
def test_the_reform_is_off_at_current_law_in_every_year(parameters, year):
    assert not switched_on(parameters, year)


rate = st.one_of(
    st.just(0.1),
    st.sampled_from([0.0, 0.05, 0.2, 1.0]),
    st.floats(min_value=0, max_value=1),
)


@settings(max_examples=60, deadline=None)
@given(
    statutory_rate=rate,
    cps_rate=rate,
    remove_income_condition=st.booleans(),
    max_child_age=st.sampled_from([0, 5, 18]),
)
def test_the_reform_switches_on_from_its_own_parameters_only(
    parameters, statutory_rate, cps_rate, remove_income_condition, max_child_age
):
    reformed = parameters.clone()
    set_value(reformed, STATUTORY_RATE, statutory_rate)
    set_value(reformed, CPS_RATE, cps_rate)
    set_value(reformed, REMOVE_INCOME_CONDITION, remove_income_condition)
    set_value(reformed, MAX_CHILD_AGE, max_child_age)
    on = switched_on(reformed)
    assert on == (remove_income_condition or cps_rate != DEFAULT_CPS_RATE)
    if statutory_rate == CURRENT_STATUTORY_RATE:
        # The switch this replaces compared the CPS rate with the statutory one.
        assert on == (remove_income_condition or cps_rate != statutory_rate)


# Invariants 2 to 5 over generated couples. One simulation per set of
# parameters, reused: each example writes its own inputs.

COUPLES = 20
# Every fourth couple lives in Scotland, whose starter and intermediate rates
# allow an election (ITA 2007 s. 55B(2)(b)).
REGIONS = ["SCOTLAND", "LONDON", "NORTH_EAST", "WALES"]


def generated_couples():
    people, benunits, households = {}, {}, {}
    for i in range(COUPLES):
        members = [f"first_{i}", f"second_{i}"]
        for member in members:
            people[member] = {
                "age": {YEAR: 40},
                "employment_income": {YEAR: 0},
                "would_claim_marriage_allowance": {YEAR: True},
            }
        benunits[f"benunit_{i}"] = {"members": members, "is_married": {YEAR: True}}
        households[f"household_{i}"] = {
            "members": members,
            "region": {YEAR: REGIONS[i % len(REGIONS)]},
        }
    return {"people": people, "benunits": benunits, "households": households}


@pytest.fixture(scope="module")
def simulation_for(cloned_uk_tax_benefit_system):
    built = {}

    def simulation_for(*pairs, reform=None):
        key = (pairs, reform)
        if key not in built:
            built[key] = Simulation(
                situation=generated_couples(),
                reform=reform if reform is not None else change(*pairs) or None,
            )
        return built[key]

    return simulation_for


income = st.one_of(
    st.floats(min_value=0, max_value=150_000),
    st.floats(min_value=0, max_value=20_000),
    # Near the band edges and allowance thresholds, UK and Scottish.
    st.sampled_from(
        [0.0, 12_570.0, 12_580.0, 15_397.0, 27_491.0, 43_662.0, 43_663.0]
        + [50_270.0, 50_271.0, 75_000.0, 100_000.0, 125_140.0, 125_141.0]
    ),
)
couple = st.tuples(
    income,
    income,
    st.sampled_from([True, True, True, False]),  # married
    st.booleans(),  # the first would claim
    st.booleans(),  # the second would claim
)
drawn_couples = st.lists(couple, min_size=COUPLES, max_size=COUPLES)
# A London earner liable at the higher rate on less than a penny: £50,270.005
# is stored as £50,270.00390625.
SUB_PENNY_ABOVE_THE_LIMIT = [(0.0, 0.0, True, True, True)] * COUPLES
SUB_PENNY_ABOVE_THE_LIMIT[1] = (50_270.005, 0.0, True, True, True)
# Statutory rates in whole thousandths. 12,570 x k / 1,000 = 12.57k is a
# multiple of £10 only at k = 0 and 1,000, and otherwise at least a penny from
# one, so float rounding cannot move the allowance across a £10 step and the
# cap below can be exact.
GRID_PERMILLE = [0, 50, 100, 150, 200, 500, 1_000]
permille = st.one_of(
    st.sampled_from(GRID_PERMILLE),
    st.integers(min_value=0, max_value=1_000),
)

SETTINGS = settings(
    max_examples=15,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)


def interleave(first, second):
    people = np.empty(2 * len(first), dtype=np.asarray(first).dtype)
    people[0::2] = first
    people[1::2] = second
    return people


def run(simulation, drawn, anyone_claims=True):
    first, second, married, first_claims, second_claims = map(np.array, zip(*drawn))
    claims = interleave(first_claims, second_claims) & anyone_claims
    simulation.set_input("employment_income", YEAR, interleave(first, second))
    simulation.set_input("is_married", YEAR, married)
    simulation.set_input("would_claim_marriage_allowance", YEAR, claims)
    simulation.reset_calculations()
    return dict(
        allowance=simulation.calculate("marriage_allowance", YEAR),
        meets_income_conditions=simulation.calculate(
            "meets_marriage_allowance_income_conditions", YEAR
        ),
        # Simulation.calculate returns an enum's names.
        band=np.asarray(simulation.calculate("tax_band", YEAR), dtype=str),
        transferable=simulation.calculate(
            "marriage_allowance_transferable_amount", YEAR
        ),
        income_tax=simulation.calculate("income_tax", YEAR),
        # The earners have only employment income, so all their taxable
        # income is non-savings income. The personal allowance is the one in
        # force, cut for a spouse who elects (s. 55B(6)).
        taxable=np.maximum(
            simulation.calculate("employment_income", YEAR)
            - simulation.calculate("personal_allowance", YEAR),
            0,
        ),
        scottish=simulation.calculate("pays_scottish_income_tax", YEAR),
    )


def statutory_cap(rate_permille):
    """The statutory share of the personal allowance, rounded up to £10."""
    increments = math.ceil(
        PERSONAL_ALLOWANCE * rate_permille / (1_000 * ROUNDING_INCREMENT)
    )
    return increments * ROUNDING_INCREMENT


@SETTINGS
@given(drawn_couples)
def test_a_zero_statutory_rate_is_no_allowance_for_anyone(simulation_for, drawn):
    zero = simulation_for((STATUTORY_RATE, 0.0))
    assert REFORM_VARIABLE not in zero.tax_benefit_system.variables
    abolished = run(zero, drawn)
    assert (abolished["allowance"] == 0).all()
    nobody_claims = run(simulation_for(), drawn, anyone_claims=False)
    np.testing.assert_array_equal(abolished["income_tax"], nobody_claims["income_tax"])


def test_taxable_income_at_the_basic_rate_limit_still_meets_the_conditions():
    # £50,270 of earnings is £37,700 of taxable income, all at the basic rate,
    # so the earner can gain; tax_band calls it higher. £50,271 is liable at
    # the higher rate on £1, and £50,270.005 (stored as £50,270.00390625) on
    # less than a penny. The same holds at the Scottish higher rate's start,
    # £43,662 of earnings in 2025-26.
    situation = couples((50_270, None), (50_271, None), (50_270.005, None))
    simulation = Simulation(situation=situation)
    assert simulation.calculate("marriage_allowance", YEAR).tolist() == [
        1_260,
        0,
        0,
        0,
        0,
        0,
    ]
    assert np.asarray(simulation.calculate("tax_band", YEAR), dtype=str)[
        0::2
    ].tolist() == ["HIGHER", "HIGHER", "HIGHER"]


@SETTINGS
@given(drawn_couples, permille)
@example(SUB_PENNY_ABOVE_THE_LIMIT, 100)
def test_any_statutory_rate_keeps_the_statutory_conditions_and_cap(
    simulation_for, drawn, rate_permille
):
    simulation = simulation_for((STATUTORY_RATE, rate_permille / 1_000))
    assert REFORM_VARIABLE not in simulation.tax_benefit_system.variables
    r = run(simulation, drawn)
    # Liable above the electing rates on any of their income, however little
    # (ITA 2007 s. 55B(2)(b), s. 55C(1)(c)). tax_band also calls taxable
    # income exactly at the limit higher, though none of it is charged at
    # the higher rate (s. 10), so it is checked one way only.
    limit = np.where(r["scottish"], SCOTTISH_HIGHER_RATE_START, BASIC_RATE_LIMIT)
    above = r["taxable"] > limit
    assert np.isin(r["band"], ["HIGHER", "ADDITIONAL"])[above].all()
    assert not r["meets_income_conditions"][above].any()
    assert r["meets_income_conditions"][~above].all()
    assert (r["allowance"][above] == 0).all()
    assert (r["allowance"] >= 0).all()
    assert (r["allowance"] <= statutory_cap(rate_permille)).all()


@settings(SETTINGS, max_examples=10)
@given(drawn_couples, permille, st.sampled_from(GRID_PERMILLE))
def test_the_transferable_amount_never_falls_as_the_statutory_rate_rises(
    simulation_for, drawn, first_permille, second_permille
):
    lower, higher = sorted([first_permille, second_permille])
    at_lower = run(simulation_for((STATUTORY_RATE, lower / 1_000)), drawn)
    at_higher = run(simulation_for((STATUTORY_RATE, higher / 1_000)), drawn)
    assert (at_lower["transferable"] <= at_higher["transferable"]).all()
    for r in (at_lower, at_higher):
        received = r["allowance"] > 0
        np.testing.assert_array_equal(
            r["allowance"][received], r["transferable"][received]
        )


def test_a_couple_can_stop_electing_as_the_statutory_rate_rises():
    # Intended: the allowance is not monotone in the rate. Earnings of £20,000
    # and £12,000 (2025-26). At 10% the £12,000 earner gives up 1,260 of
    # allowance, paying 20% x (12,000 - 11,310) = 138 for the partner's 252.
    # At 100% they give up all 12,570 and would pay 2,400 for a reduction
    # capped at the partner's tax, 20% x (20,000 - 12,570) = 1,486, so no one
    # elects.
    situation = couples((20_000, None))
    situation["people"]["partner_0"]["employment_income"] = {YEAR: 12_000}
    at_ten = Simulation(situation=situation)
    at_full = Simulation(situation=situation, reform=change((STATUTORY_RATE, 1.0)))
    assert at_ten.calculate("marriage_allowance", YEAR).tolist() == [1_260, 0]
    assert at_full.calculate("marriage_allowance", YEAR).tolist() == [0, 0]
    assert at_full.calculate(
        "marriage_allowance_transferable_amount", YEAR
    ).tolist() == [12_570, 12_570]


@SETTINGS
@given(drawn_couples)
def test_the_switched_on_reform_is_the_expanded_reform(simulation_for, drawn):
    switched = run(simulation_for((REMOVE_INCOME_CONDITION, True)), drawn)
    explicit = run(simulation_for(reform=expanded_ma_reform), drawn)
    for variable in ("allowance", "meets_income_conditions", "income_tax"):
        np.testing.assert_array_equal(switched[variable], explicit[variable])
