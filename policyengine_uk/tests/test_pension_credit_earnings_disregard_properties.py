"""Properties of the Pension Credit earnings disregards (SPC Regs 2002 Sch VI).

Invariants, over generated benefit units in England and Scotland:

1. Statute: the disregard equals min(net earnings, 52 x w). Net earnings are
   the claimant's and partner's gross earnings less earnings NI, half of
   pension contributions and income tax on the earnings. The tax on a
   person's earnings is measured independently, as the fall in their income
   tax when the simulation is rerun without their earnings (the earnings as
   the top slice, on their own Scottish or rest-of-UK schedule). w is 20 if
   the unit is a lone-parent family, or a claimant or partner is entitled to
   carer's allowance (an input here), receives a listed
   disability benefit or is blind; otherwise 5 single, 10 couple. A dependent
   child's DLA or caring never qualifies.
2. Bounds: 0 <= disregard <= min(gross earnings, 20 x 52).
3. Differential: Pension Credit income is the pre-change income (sources less
   tax, NI and half of pension contributions, floored at 0) less the
   disregard, floored at 0.
4. Monotonicity: the guarantee credit is never below its value without the
   disregard.
5. Earning more never raises Pension Credit entitlement (reg 17(9) applies the
   disregard to net earnings).
6. The dated benefit lists follow the amending instruments: ESA from 27
   October 2008, PIP and AFIP from 8 April 2013.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.model_api import WEEKS_IN_YEAR

YEAR = 2024
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
            "age": draw(st.sampled_from([67, 72, 85])),
            "employment_income": draw(st.sampled_from([0, 50, 400, 1_040, 3_000])),
            "self_employment_income": draw(st.sampled_from([0, 0, 1_500])),
            "state_pension": draw(st.integers(min_value=0, max_value=12_000)),
            "private_pension_income": draw(st.sampled_from([0, 2_000, 6_000])),
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
    return Simulation(
        situation={
            "people": dated,
            "benunits": {"b": {"members": members}},
            "households": {
                "h": {"members": members, "country": {str(YEAR): case["country"]}}
            },
        }
    )


def without_earnings(case, name):
    people = {n: dict(p) for n, p in case["people"].items()}
    people[name]["employment_income"] = 0
    people[name]["self_employment_income"] = 0
    return {"people": people, "country": case["country"]}


def unit_value(sim, variable):
    return float(sim.calculate(variable, YEAR)[0])


def person_values(sim, variable):
    return np.asarray(sim.calculate(variable, YEAR, map_to="person"), dtype=float)


@SETTINGS
@given(units())
def test_statute_bounds_differential_and_monotonicity(case):
    people = case["people"]
    sim = simulate(case)
    names = list(people)
    adults = [n != "child" for n in names]
    gross = np.array(
        [
            people[n]["employment_income"] + people[n].get("self_employment_income", 0)
            if n != "child"
            else 0
            for n in names
        ],
        dtype=float,
    )
    ni = sum(
        person_values(sim, v)
        for v in ["ni_class_1_employee", "ni_class_2", "ni_class_4"]
    )
    income_tax = person_values(sim, "income_tax")
    tax_on_earnings = np.zeros(len(names))
    for i, name in enumerate(names):
        if gross[i] > 0:
            rerun = person_values(simulate(without_earnings(case, name)), "income_tax")
            tax_on_earnings[i] = max(0.0, income_tax[i] - rerun[i])
    contributions = 0.5 * person_values(sim, "pension_contributions")
    net = np.maximum(0, gross - ni - tax_on_earnings - contributions)
    net_earnings = float(net[adults].sum())

    adult_people = [people[n] for n in names if n != "child"]
    couple = len(adult_people) == 2
    disabled = any(
        p.get("is_blind") or any(p.get(b, 0) > 0 for b in DISABILITY)
        for p in adult_people
    )
    carer = any(p.get("is_entitled_to_carer_benefit") for p in adult_people)
    lone_parent = "child" in people and not couple
    weekly = 20 if (disabled or carer or lone_parent) else (10 if couple else 5)
    expected = min(net_earnings, weekly * WEEKS_IN_YEAR)
    disregard = unit_value(sim, "pension_credit_earnings_disregard")
    assert np.isclose(disregard, expected, atol=0.01)
    assert 0 <= disregard <= min(gross.sum(), 20 * WEEKS_IN_YEAR) + 0.01

    sources = sim.tax_benefit_system.parameters(
        f"{YEAR}-06-01"
    ).gov.dwp.pension_credit.guarantee_credit.income
    total = sum(float(sim.calculate(s, YEAR, map_to="benunit")[0]) for s in sources)
    deductions = (
        float(sim.calculate("income_tax", YEAR, map_to="benunit")[0])
        + float(sim.calculate("national_insurance", YEAR, map_to="benunit")[0])
        + 0.5 * float(sim.calculate("pension_contributions", YEAR, map_to="benunit")[0])
    )
    before = max(0.0, total - deductions)
    assert np.isclose(
        unit_value(sim, "pension_credit_income"),
        max(0.0, before - disregard),
        atol=0.01,
    )
    gc_without = max(0.0, unit_value(sim, "minimum_guarantee") - before)
    assert unit_value(sim, "guarantee_credit") >= gc_without - 0.01


@SETTINGS
@given(units(), st.sampled_from([1, 50, 260, 1_040, 5_000]))
def test_earning_more_never_raises_pension_credit(case, extra):
    more = {name: dict(person) for name, person in case["people"].items()}
    more["claimant"]["employment_income"] += extra
    before = unit_value(simulate(case), "pension_credit_entitlement")
    after = unit_value(
        simulate({"people": more, "country": case["country"]}),
        "pension_credit_entitlement",
    )
    assert after <= before + 0.01


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
