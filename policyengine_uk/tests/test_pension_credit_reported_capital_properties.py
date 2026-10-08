"""Properties of the Pension Credit reported-capital override.

`pension_credit_reported_capital` (benefit unit, default -1) replaces the
household proxy in `pension_credit_assessable_capital` when it is 0 or more.
Pension Credit counts the claimant's capital and, under the State Pension
Credit Act 2002 s. 5, the partner's, which a survey's benefit-unit capital
measure records directly.

Invariants, over generated households of one or two benefit units:

1. Override identity: a pension-age unit with reported capital R >= 0 has
   assessable capital R, whatever the household holds.
2. Default differential: with nothing reported, assessable capital equals the
   household proxy recomputed here from the inputs (household sources times
   the unit's share of the household's pension-age adults, plus person-level
   sources of the claimant or partner), the formula before this change.
3. Locality: reporting capital for one unit never changes another unit's
   assessable capital. The strategy for this property always gives the other
   unit someone over State Pension age, nothing recorded and household capital,
   so a leak would show.
4. Bounds: assessable capital is never negative, and is 0 for a unit with no
   one over State Pension age.
5. Monotonicity: the guarantee credit never rises with reported capital, and
   nor does total entitlement when all income is savings credit qualifying
   income (the generated households have no excluded income).
   Intended exception (SPCA 2002 s. 3): with income that the savings credit
   excludes (reg. 9), such as contributory ESA, deemed income from capital
   phases the savings credit in at 60% but tapers it at only 40% above the
   minimum guarantee, so entitlement can rise with capital. A pinned case
   checks that it does.
6. Deemed income: for reported capital R it is ceil(max(0, R - 10,000) / 500)
   pounds a week (SPC Regs 2002 reg 15(6)).
"""

import math

import numpy as np
import yaml
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.model_api import WEEKS_IN_YEAR

YEAR = 2025
SETTINGS = settings(
    max_examples=20,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
money = st.integers(min_value=0, max_value=200_000)
ages = st.sampled_from([30, 50, 67, 72, 80, 90])
reported = st.one_of(st.just(-1), st.integers(min_value=0, max_value=60_000))


@st.composite
def households(draw):
    two_units = draw(st.booleans())
    units = []
    people = {}
    for u in range(2 if two_units else 1):
        size = draw(st.integers(min_value=1, max_value=2))
        names = [f"p{u}_{i}" for i in range(size)]
        for name in names:
            people[name] = {
                "age": draw(ages),
                "state_pension": draw(st.integers(min_value=0, max_value=12_000)),
                "lifetime_isa_countable_capital": draw(st.sampled_from([0, 0, 5_000])),
            }
        units.append({"members": names, "reported": draw(reported)})
    household = {
        "savings": draw(money),
        "owned_land": draw(st.sampled_from([0, 0, 25_000])),
        "corporate_wealth": draw(st.sampled_from([0, 40_000])),
    }
    return people, units, household


def simulate(people, units, household, overrides=None):
    year = str(YEAR)
    benunits = {}
    for i, unit in enumerate(units):
        value = unit["reported"] if overrides is None else overrides[i]
        benunits[f"b{i}"] = {
            "members": unit["members"],
            "pension_credit_reported_capital": {year: value},
        }
    situation = {
        "people": {
            name: {k: {year: v} for k, v in person.items()}
            for name, person in people.items()
        },
        "benunits": benunits,
        "households": {
            "h": {
                "members": list(people),
                **{k: {year: v} for k, v in household.items()},
            }
        },
    }
    return Simulation(situation=situation)


def proxy(people, units, household, index):
    """Assessable capital before this change, recomputed from inputs."""
    sources = [
        "savings",
        "owned_land",
        "other_residential_property_value",
        "non_residential_property_value",
        "corporate_wealth",
    ]
    household_capital = sum(household.get(s, 0) for s in sources)
    sp_age = {name: p["age"] >= 66 for name, p in people.items()}
    unit = units[index]["members"]
    unit_sp = sum(sp_age[n] for n in unit)
    household_sp = sum(sp_age.values())
    if unit_sp == 0:
        return 0.0
    person = sum(
        people[n]["lifetime_isa_countable_capital"]
        for n in unit
        if people[n]["age"] >= 18
    )
    return household_capital * unit_sp / max(1, household_sp) + person


@SETTINGS
@given(households())
def test_override_default_bounds_and_deemed_income(case):
    people, units, household = case
    sim = simulate(people, units, household)
    capital = sim.calculate("pension_credit_assessable_capital", YEAR)
    deemed = sim.calculate("pension_credit_deemed_income", YEAR)
    for i, unit in enumerate(units):
        any_sp = any(people[n]["age"] >= 66 for n in unit["members"])
        assert capital[i] >= 0
        if not any_sp:
            assert capital[i] == 0
        elif unit["reported"] >= 0:
            assert capital[i] == unit["reported"]
            steps = math.ceil(max(0, unit["reported"] - 10_000) / 500)
            assert deemed[i] == np.float32(steps * WEEKS_IN_YEAR)
        else:
            assert np.isclose(capital[i], proxy(people, units, household, i), rtol=1e-6)


@st.composite
def two_unit_households(draw):
    """Two units; the second has someone over State Pension age, records no
    capital and shares non-zero household capital, so a leak would show."""
    people = {
        "a0": {"age": draw(ages), "state_pension": draw(money)},
        "b0": {"age": draw(st.sampled_from([67, 72, 80, 90])), "state_pension": 0},
    }
    if draw(st.booleans()):
        people["b1"] = {"age": draw(ages), "state_pension": 0}
    for person in people.values():
        person["lifetime_isa_countable_capital"] = draw(st.sampled_from([0, 5_000]))
    units = [
        {"members": ["a0"], "reported": -1},
        {"members": [n for n in people if n.startswith("b")], "reported": -1},
    ]
    household = {
        "savings": draw(st.integers(min_value=1_000, max_value=200_000)),
        "owned_land": draw(st.sampled_from([0, 25_000])),
        "corporate_wealth": draw(st.sampled_from([0, 40_000])),
    }
    return people, units, household


@SETTINGS
@given(two_unit_households(), st.integers(min_value=0, max_value=60_000))
def test_locality(case, value):
    people, units, household = case
    before = simulate(people, units, household, overrides=[-1, -1])
    after = simulate(people, units, household, overrides=[value, -1])
    assert before.calculate("pension_credit_assessable_capital", YEAR)[1] > 0
    assert np.isclose(
        before.calculate("pension_credit_assessable_capital", YEAR)[1],
        after.calculate("pension_credit_assessable_capital", YEAR)[1],
    )


@SETTINGS
@given(
    households(),
    st.integers(min_value=0, max_value=60_000),
    st.integers(min_value=0, max_value=60_000),
)
def test_entitlement_never_rises_with_reported_capital(case, a, b):
    # The generated households have no income the savings credit excludes,
    # so total entitlement is monotone here; see the intended exception below.
    people, units, household = case
    low, high = sorted([a, b])
    overrides_low = [low] + [u["reported"] for u in units[1:]]
    overrides_high = [high] + [u["reported"] for u in units[1:]]
    low_sim = simulate(people, units, household, overrides_low)
    high_sim = simulate(people, units, household, overrides_high)
    for variable in ["guarantee_credit", "pension_credit_entitlement"]:
        assert (
            high_sim.calculate(variable, YEAR)[0]
            <= low_sim.calculate(variable, YEAR)[0] + 1e-6
        )


def test_intended_exception_savings_credit_rises_with_capital():
    """SPCA 2002 s. 3: with income the savings credit excludes (contributory
    ESA, reg. 9), 500 pounds more capital adds 1 pound a week of deemed income
    to both incomes: amount A rises by 60p and amount B by 40p, so the savings
    credit rises by 20p a week (10.40 a year)."""

    def entitlement(capital):
        sim = Simulation(
            situation={
                "people": {
                    "p": {
                        "age": {str(YEAR): 80},
                        "state_pension": {str(YEAR): 10_900},
                        "esa_contrib": {str(YEAR): 1_300},
                    }
                },
                "benunits": {
                    "b": {
                        "members": ["p"],
                        "pension_credit_reported_capital": {str(YEAR): capital},
                    }
                },
                "households": {"h": {"members": ["p"]}},
            }
        )
        return sim.calculate("pension_credit_entitlement", YEAR)[0]

    assert np.isclose(entitlement(10_500) - entitlement(10_000), 0.2 * WEEKS_IN_YEAR)


def test_reported_capital_uprates_with_savings():
    from pathlib import Path

    from policyengine_uk.system import system

    variables = system.variables
    # The variable is a formula of benunit_reported_capital, which carries the
    # uprating; a dataset that stores it directly is uprated through
    # uprating_indices.yaml.
    assert (
        variables["benunit_reported_capital"].uprating == variables["savings"].uprating
    )
    assert variables["pension_credit_reported_capital"].default_value == -1
    indices = yaml.safe_load(
        (Path(__file__).parents[1] / "data" / "uprating_indices.yaml").read_text()
    )
    group = [k for k, v in indices.items() if "savings" in v]
    assert len(group) == 1
    assert "pension_credit_reported_capital" in indices[group[0]]
