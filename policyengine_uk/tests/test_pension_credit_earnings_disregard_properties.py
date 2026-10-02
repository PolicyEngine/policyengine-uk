"""Properties of the Pension Credit earnings disregards (SPC Regs 2002 Sch VI).

Invariants, over generated pension-age benefit units:

1. Statute: the disregard equals min(earnings, 52 x w), where w is 20 if the
   unit has a lone parent, a carer satisfying Sch I para 4, or a claimant or
   partner on a listed disability benefit or certified blind, and otherwise 5
   for a single claimant and 10 for a couple. The expected value is computed
   here from the inputs, not read from the model.
2. Bounds: 0 <= disregard <= min(earnings, 20 x 52).
3. Differential: Pension Credit income is the pre-change income (sources less
   tax, NI and half of pension contributions, floored at 0, recomputed from
   the model's own components) less the disregard, floored at 0.
4. Monotonicity: the guarantee credit never falls when the disregard applies,
   i.e. it is at least the guarantee credit without it.
5. The dated benefit lists follow the amending instruments: ESA from 27
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
    couple = draw(st.booleans())
    child = draw(st.booleans()) and not couple
    people = {}
    names = ["claimant"] + (["partner"] if couple else [])
    for n in names:
        person = {
            "age": draw(st.sampled_from([67, 72, 85])),
            "employment_income": draw(st.sampled_from([0, 50, 400, 3_000])),
            "self_employment_income": draw(st.sampled_from([0, 0, 1_500])),
            "state_pension": draw(st.integers(min_value=0, max_value=12_000)),
            "private_pension_income": draw(st.sampled_from([0, 2_000])),
            "is_blind": draw(st.sampled_from([False, False, False, True])),
            "is_carer_for_benefits": draw(st.sampled_from([False, False, False, True])),
        }
        benefit = draw(st.sampled_from([None, None] + DISABILITY))
        if benefit:
            person[benefit] = 2_000
        people[n] = person
    if child:
        people["child"] = {"age": 10, "dla_sc": draw(st.sampled_from([0, 2_000]))}
    return people


def simulate(people):
    members = list(people)
    dated = {
        name: {k: {str(YEAR): v} for k, v in person.items()}
        for name, person in people.items()
    }
    return Simulation(
        situation={
            "people": dated,
            "benunits": {"b": {"members": members}},
            "households": {"h": {"members": members}},
        }
    )


@SETTINGS
@given(units())
def test_statute_bounds_differential_and_monotonicity(people):
    sim = simulate(people)
    calc = lambda v: float(sim.calculate(v, YEAR)[0])
    adults = [p for n, p in people.items() if n != "child"]
    earnings = sum(p["employment_income"] + p["self_employment_income"] for p in adults)
    couple = len(adults) == 2
    disabled = any(
        p.get("is_blind") or any(p.get(b, 0) > 0 for b in DISABILITY) for p in adults
    )
    carer = calc("carer_minimum_guarantee_addition") > 0
    lone_parent = "child" in people
    weekly = 20 if (disabled or carer or lone_parent) else (10 if couple else 5)
    expected = min(earnings, weekly * WEEKS_IN_YEAR)
    disregard = calc("pension_credit_earnings_disregard")
    assert np.isclose(disregard, expected, atol=0.01)
    assert 0 <= disregard <= min(earnings, 20 * WEEKS_IN_YEAR) + 0.01

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
        calc("pension_credit_income"), max(0.0, before - disregard), atol=0.01
    )
    gc_without = max(0.0, calc("minimum_guarantee") - before)
    assert calc("guarantee_credit") >= gc_without - 0.01


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
