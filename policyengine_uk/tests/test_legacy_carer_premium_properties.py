"""The legacy carer premium and the Income Support carer route follow only the
claimant and partner.

IS Regs 1987 Sch 2 para 14ZA(1) (and the JSA, ESA, HB and CTR equivalents)
give the carer premium where "the claimant or his partner is, or both of them
are" entitled to Carer's Allowance or Carer Support Payment, and para 15(7)
pays it "in respect of each person who satisfied the condition". The Income
Support carer route (Sch 1B para 4, reg 4ZA, SSCBA s.124(1)(e)) likewise
needs the claimant to be the carer, and a couple choose which of them claims.

Invariants, for any family of a claimant, an optional partner and up to three
dependent children or qualifying young persons:

- a dependant's caring never changes carer_premium or income_support_eligible;
- carer_premium equals the per-person amount, weekly x 52, times the number
  of caring claimants and partners, so it is 0, one amount or two;
- caring by the claimant or partner never removes Income Support eligibility.

Each example builds every family twice in one simulation, in separate
households and benefit units: once as drawn and once with a changed caring
pattern.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

YEAR = 2026
WEEKS = 52


@st.composite
def carer_inputs(draw):
    # Either limb of is_carer_for_benefits: a carer benefit, or 35+ hours.
    return {
        "receives_carer_benefit": draw(st.booleans()),
        "care_hours": draw(st.sampled_from([0, 20, 34, 35, 50])),
    }


@st.composite
def families(draw):
    n_dependants = draw(st.integers(0, 3))
    dependants = []
    for _ in range(n_dependants):
        if draw(st.booleans()):
            dependant = {"age": draw(st.integers(0, 15))}
        else:
            # A qualifying young person: 16-19 in non-advanced education.
            dependant = {
                "age": draw(st.integers(16, 19)),
                "current_education": "UPPER_SECONDARY",
            }
        dependants.append({**dependant, **draw(carer_inputs())})
    youngest = max([d["age"] for d in dependants], default=0)
    head_age = draw(st.integers(max(25, youngest + 16), 60))
    has_parent_flag = n_dependants > 0
    head = {
        "age": head_age,
        "is_parent": has_parent_flag,
        "income_support_reported": 1_000,
        **draw(carer_inputs()),
    }
    family = [head]
    if draw(st.booleans()):
        family.append(
            {
                "age": draw(st.integers(25, 60)),
                "is_parent": has_parent_flag,
                **draw(carer_inputs()),
            }
        )
    return family + dependants, len(family)


def situation(units):
    people, benunits, households = {}, {}, {}
    for i, family in enumerate(units):
        names = []
        for j, inputs in enumerate(family):
            name = f"p{i}_{j}"
            people[name] = {k: {YEAR: v} for k, v in inputs.items()}
            names.append(name)
        benunits[f"b{i}"] = {
            "members": names,
            "esa_income": {YEAR: 0},
            "income_support_assessable_capital": {YEAR: 0},
        }
        households[f"h{i}"] = {"members": names}
    return {"people": people, "benunits": benunits, "households": households}


NOT_CARING = {"receives_carer_benefit": False, "care_hours": 0}
CARING = {"receives_carer_benefit": True, "care_hours": 35}

SETTINGS = settings(
    max_examples=15,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)


@SETTINGS
@given(st.lists(families(), min_size=1, max_size=6))
def test_dependants_caring_never_changes_premium_or_is_eligibility(drawn):
    units = [family for family, _ in drawn]
    adults = [n for _, n in drawn]
    without = [
        family[:n] + [{**member, **NOT_CARING} for member in family[n:]]
        for family, n in zip(units, adults)
    ]
    sim = Simulation(situation=situation(units + without))
    flags = sim.calculate("is_claimant_or_partner", YEAR)
    carers = sim.calculate("is_carer_for_benefits", YEAR)
    offsets = np.cumsum([0] + [len(f) for f in units + without])
    for i, n in enumerate(adults):
        # The generator's construction, checked against the model: the first
        # n members are the claimant and partner, the rest are dependants.
        members = flags[offsets[i] : offsets[i + 1]]
        assert members[:n].all() and not members[n:].any(), units[i]
    premium = sim.calculate("carer_premium", YEAR)
    eligible = sim.calculate("income_support_eligible", YEAR)
    amount = sim.tax_benefit_system.parameters(YEAR).gov.dwp.carer_premium.single
    k = len(units)
    for i, n in enumerate(adults):
        assert abs(premium[i] - premium[k + i]) < 0.01, units[i]
        assert eligible[i] == eligible[k + i], units[i]
        qualifying = carers[offsets[i] : offsets[i] + n].sum()
        assert abs(premium[i] - qualifying * amount * WEEKS) < 0.01, units[i]
        assert 0 <= premium[i] <= 2 * amount * WEEKS + 0.01, units[i]


@SETTINGS
@given(st.lists(families(), min_size=1, max_size=6), st.data())
def test_claimant_or_partner_caring_never_removes_is_eligibility(drawn, data):
    units = [family for family, _ in drawn]
    adults = [n for _, n in drawn]
    # Make one of the claimant and partner a carer.
    with_caring = []
    for family, n in zip(units, adults):
        who = data.draw(st.integers(0, n - 1))
        with_caring.append(
            [
                {**member, **CARING} if j == who else member
                for j, member in enumerate(family)
            ]
        )
    sim = Simulation(situation=situation(units + with_caring))
    eligible = sim.calculate("income_support_eligible", YEAR)
    premium = sim.calculate("carer_premium", YEAR)
    k = len(units)
    for i in range(k):
        assert eligible[k + i] >= eligible[i], units[i]
        assert eligible[k + i], units[i]
        assert premium[k + i] >= premium[i] - 0.01, units[i]
