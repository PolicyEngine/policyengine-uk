"""Properties of the Pension Credit earnings disregards (SPC Regs 2002 Sch VI)
and of the net earnings they apply to (regs. 17(10), 17(11), 17A and 17B).

Invariants, over generated benefit units in England and Scotland:

1. Statute: the disregard equals min(net earnings, 52 x w), recomputed here
   from the inputs and independent simulations:
   - each person's own earnings, each source floored at nil, less their
     primary Class 1 contributions, half of their pension contributions and,
     on self-employed profit, the notional tax and contributions of CER 1996
     reg. 14 (basic rate on the profit less the personal allowance and any
     marriage allowance; main-rate Class 4 under State Pension age), floored
     at nil;
   - less the income tax payable on the claimant's and partner's employed
     earnings, measured as the fall in their income tax when the household
     is simulated again with nobody's employment income.
   w is 20 if the unit is a lone-parent family, or a claimant or partner is
   entitled to carer's allowance (an input here), receives a listed
   disability benefit or is blind; otherwise 5 single, 10 couple. A dependent
   child's DLA or caring never qualifies.
2. Bounds: 0 <= disregard <= min(gross earnings, 20 x 52).
3. Differential: Pension Credit income is the sources less tax, NI and half
   of pension contributions, with the tax and contributions actually payable
   on self-employed profit replaced by the notional ones, floored at 0, less
   the disregard, floored at 0.
4. Monotonicity: the guarantee credit is never below its value without the
   disregard (for units with nobody under State Pension age).
5. Earning more, employed or self-employed, by either partner, never raises
   Pension Credit.
6. Under the disregard, Pension Credit income does not change with earnings.
7. The dated benefit lists follow the amending instruments: ESA from 27
   October 2008, PIP and AFIP from 8 April 2013.
8. The Scottish basic rate read for the notional tax is 20% in every year,
   including those before the starter rate.
"""

import numpy as np
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.model_api import WEEKS_IN_YEAR

YEAR = 2024
BASIC_RATE = 0.2
PERSONAL_ALLOWANCE = 12_570
CLASS_4_MAIN_RATE = 0.06
LOWER_PROFITS_LIMIT = 12_570
UPPER_PROFITS_LIMIT = 50_270
STATE_PENSION_AGE = 66
SETTINGS = settings(
    max_examples=25,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
DISABILITY = [
    "attendance_allowance",
    "dla_sc",
    "pip_dl",
    "incapacity_benefit",
    "esa_contrib",
]


@st.composite
def units(draw):
    country = draw(st.sampled_from(["ENGLAND", "SCOTLAND"]))
    couple = draw(st.booleans())
    child = draw(st.booleans())
    people = {}
    names = ["claimant"] + (["partner"] if couple else [])
    for n in names:
        person = {
            "age": draw(
                st.sampled_from([67, 72, 85] + ([64] if n == "partner" else []))
            ),
            "employment_income": draw(st.sampled_from([0, 50, 400, 1_040, 3_000])),
            "self_employment_income": draw(
                st.sampled_from([0, 0, 1_500, 15_000, -2_000])
            ),
            "state_pension": draw(st.integers(min_value=0, max_value=12_000)),
            "private_pension_income": draw(st.sampled_from([0, 2_000, 6_000])),
            "savings_interest_income": draw(st.sampled_from([0, 0, 3_000])),
            "is_blind": draw(st.sampled_from([False, False, False, True])),
            "is_entitled_to_carer_benefit": draw(
                st.sampled_from([False, False, False, True])
            ),
            "care_hours": draw(st.sampled_from([0, 0, 40])),
            "personal_pension_contributions": draw(st.sampled_from([0, 0, 300])),
        }
        benefit = draw(st.sampled_from([None, None] + DISABILITY))
        if benefit:
            person[benefit] = 2_000
        people[n] = person
    if child:
        # A dependent child's DLA or caring never qualifies the unit.
        people["child"] = {
            "age": 10,
            "dla_sc": draw(st.sampled_from([0, 2_000])),
            "is_entitled_to_carer_benefit": draw(st.booleans()),
        }
    return {"people": people, "country": country}


def simulate(case):
    people = case["people"]
    members = list(people)
    dated = {
        name: {k: {str(YEAR): v} for k, v in person.items()}
        for name, person in people.items()
    }
    # The claimant and partner say so: the age presumption would read a
    # partner 20 or more years younger (85 and 64) as the claimant's child.
    for name, person in dated.items():
        person["is_claimant_or_partner"] = {str(YEAR): name != "child"}
    return Simulation(
        situation={
            "people": dated,
            "benunits": {"b": {"members": members}},
            "households": {
                "h": {"members": members, "country": {str(YEAR): case["country"]}}
            },
        }
    )


def without(case, sources):
    """The case with nobody's income from each of ``sources``."""
    people = {n: dict(p) for n, p in case["people"].items()}
    for person in people.values():
        for source in sources:
            if source in person:
                person[source] = 0
    return {"people": people, "country": case["country"]}


def unit_value(sim, variable):
    return float(sim.calculate(variable, YEAR)[0])


def person_values(sim, variable):
    return np.asarray(sim.calculate(variable, YEAR, map_to="person"), dtype=float)


def weekly_amount(people):
    adult_people = [p for n, p in people.items() if n != "child"]
    couple = len(adult_people) == 2
    disabled = any(
        p.get("is_blind") or any(p.get(b, 0) > 0 for b in DISABILITY)
        for p in adult_people
    )
    carer = any(p.get("is_entitled_to_carer_benefit") for p in adult_people)
    lone_parent = "child" in people and not couple
    return 20 if (disabled or carer or lone_parent) else (10 if couple else 5)


def notional_deductions(person, marriage_allowance):
    """CER 1996 reg. 14 on the person's profit, from the inputs: no
    generated adult is blind-person's-allowance relieved, born before 1935
    or liable for Class 2 (abolished in 2024-25)."""
    profit = max(0, person.get("self_employment_income", 0))
    if profit == 0:
        return 0.0
    tax = BASIC_RATE * max(0, profit - PERSONAL_ALLOWANCE - marriage_allowance)
    class_4 = 0.0
    if person["age"] < STATE_PENSION_AGE:
        class_4 = CLASS_4_MAIN_RATE * min(
            max(0, profit - LOWER_PROFITS_LIMIT),
            UPPER_PROFITS_LIMIT - LOWER_PROFITS_LIMIT,
        )
    return tax + class_4


@SETTINGS
@given(units())
def test_statute_bounds_differential_and_monotonicity(case):
    people = case["people"]
    sim = simulate(case)
    names = list(people)
    adult = np.array([n != "child" for n in names])
    employment = np.array(
        [max(0, people[n].get("employment_income", 0)) for n in names], dtype=float
    )
    self_employment = np.array(
        [max(0, people[n].get("self_employment_income", 0)) for n in names],
        dtype=float,
    )
    marriage_allowance = person_values(sim, "marriage_allowance")
    notional = np.array(
        [
            notional_deductions(people[n], marriage_allowance[i])
            for i, n in enumerate(names)
        ]
    )
    assert np.allclose(
        person_values(sim, "pension_credit_self_employment_deductions"),
        notional,
        atol=0.01,
    )
    class_1 = person_values(sim, "ni_class_1_employee")
    contributions = 0.5 * person_values(sim, "pension_contributions")
    own_net = np.maximum(
        0, employment + self_employment - class_1 - notional - contributions
    )

    income_tax = person_values(sim, "income_tax")
    no_employment = person_values(
        simulate(without(case, ["employment_income"])), "income_tax"
    )
    no_earnings = person_values(
        simulate(without(case, ["employment_income", "self_employment_income"])),
        "income_tax",
    )
    employment_tax = max(0.0, float((income_tax - no_employment)[adult].sum()))
    self_employment_tax = max(0.0, float((no_employment - no_earnings)[adult].sum()))
    net_earnings = max(0.0, float(own_net[adult].sum()) - employment_tax)

    expected = min(net_earnings, weekly_amount(people) * WEEKS_IN_YEAR)
    disregard = unit_value(sim, "pension_credit_earnings_disregard")
    assert np.isclose(disregard, expected, atol=0.01)
    gross = float((employment + self_employment)[adult].sum())
    assert 0 <= disregard <= min(gross, 20 * WEEKS_IN_YEAR) + 0.01

    sources = sim.tax_benefit_system.parameters(
        f"{YEAR}-06-01"
    ).gov.dwp.pension_credit.guarantee_credit.income
    total = sum(float(sim.calculate(s, YEAR, map_to="benunit")[0]) for s in sources)
    actual_self_employment = (
        self_employment_tax
        + float(person_values(sim, "ni_class_2")[adult].sum())
        + float(person_values(sim, "ni_class_4")[adult].sum())
    )
    deductions = (
        float(income_tax[adult].sum())
        + float(person_values(sim, "national_insurance")[adult].sum())
        - actual_self_employment
        + float(notional[adult].sum())
        + float(contributions[adult].sum())
    )
    before = max(0.0, total - deductions)
    assert np.isclose(
        unit_value(sim, "pension_credit_income"),
        max(0.0, before - disregard),
        atol=0.01,
    )
    # Mixed-age couples (a partner under State Pension age) get no guarantee
    # credit at all, so the comparison is for units entirely over that age.
    if all(p["age"] >= STATE_PENSION_AGE for n, p in people.items() if n != "child"):
        gc_without = max(0.0, unit_value(sim, "minimum_guarantee") - before)
        assert unit_value(sim, "guarantee_credit") >= gc_without - 0.01


EARNINGS_RISES = st.tuples(
    st.sampled_from(["claimant", "partner"]),
    st.sampled_from(["employment_income", "self_employment_income"]),
    st.sampled_from([1, 50, 260, 1_040, 5_000]),
)


def raised(case, rise):
    name, source, extra = rise
    if name not in case["people"]:
        name = "claimant"
    people = {n: dict(p) for n, p in case["people"].items()}
    people[name][source] = people[name].get(source, 0) + extra
    return {"people": people, "country": case["country"]}


@SETTINGS
@given(units(), EARNINGS_RISES)
def test_earning_more_never_raises_pension_credit(case, rise):
    before = unit_value(simulate(case), "pension_credit_entitlement")
    after = unit_value(simulate(raised(case, rise)), "pension_credit_entitlement")
    assert after <= before + 0.01


@st.composite
def units_under_the_disregard(draw):
    """Units with small earnings and no pension contributions or losses, so
    the disregard usually covers the net earnings and no floor on a person's
    net earnings binds."""
    case = draw(units())
    for person in case["people"].values():
        person.pop("personal_pension_contributions", None)
        if "employment_income" in person:
            person["employment_income"] = draw(st.sampled_from([0, 50, 100]))
            person["self_employment_income"] = draw(st.sampled_from([0, 0, 120]))
    return case


@settings(SETTINGS, suppress_health_check=list(HealthCheck))
@given(
    units_under_the_disregard(),
    st.tuples(
        st.sampled_from(["claimant", "partner"]),
        st.sampled_from(["employment_income", "self_employment_income"]),
        st.sampled_from([1, 50, 100]),
    ),
)
def test_pension_credit_income_is_flat_in_earnings_under_the_disregard(case, rise):
    sims = [simulate(case), simulate(raised(case, rise))]
    cap = weekly_amount(case["people"]) * WEEKS_IN_YEAR
    # Where the disregard covers all the net earnings before and after the
    # rise, and Pension Credit income is not floored at nil.
    assume(
        all(
            unit_value(sim, "pension_credit_earnings_disregard") < cap - 0.01
            and unit_value(sim, "pension_credit_income") > 0
            for sim in sims
        )
    )
    before, after = (unit_value(sim, "pension_credit_income") for sim in sims)
    assert np.isclose(before, after, atol=0.05)


def test_benefit_lists_follow_amending_instruments():
    from policyengine_uk.system import system

    def lists(date):
        p = system.parameters(date).gov.dwp.pension_credit.earnings_disregard.higher
        return set(p.disability_benefits), set(p.disability_benefit_unit_benefits)

    person, unit = lists("2008-10-26")
    assert "esa_contrib" not in person and "esa_income" not in unit
    person, unit = lists("2008-10-27")
    assert "esa_contrib" in person and "esa_income" in unit
    person, _ = lists("2013-04-07")
    assert "pip" not in person and "armed_forces_independence_payment" not in person
    person, _ = lists("2013-04-08")
    assert {"pip", "armed_forces_independence_payment"} <= person
    for date in ["2008-10-26", "2013-04-08", "2026-04-06"]:
        person, _ = lists(date)
        assert {"incapacity_benefit", "sda", "attendance_allowance", "dla"} <= person


def test_scottish_basic_rate_band_is_twenty_percent_in_every_year():
    from policyengine_uk.system import system

    bands = system.parameters.gov.hmrc.income_tax.rates.scotland.rates.brackets
    for year in range(2016, 2030):
        assert bands[1].rate(f"{year}-06-01") == 0.2
