"""Income Support eligibility follows only the claimant and partner.

SSCBA 1992 s.124(1) sets each condition for the claimant ("he") and, in
paras (c), (f), (g) and (h), for "the other member of the couple". A couple
choose which of them claims (Claims and Payments Regs 1987 reg 4(3)). Nobody
else in a benefit unit is named, so:

- adding a member who is neither the claimant, the partner nor a child or
  young person they are responsible for never changes income_support_eligible,
  whatever that member's age, ESA, Income Support or caring;
- income_support_eligible equals a direct reading of the conditions: one of
  the claimant and partner is under state pension age, is a carer (or a lone
  parent of a child aged 5 or under, the model's reading of Sch 1B para 1)
  and has no contributory ESA (s.124(1)(aa), (e), (h)); neither has
  income-related ESA after the ESA capital test (s.124(1)(h)); one of them
  reports an existing award (UC (Transitional Provisions) Regs 2014 reg 6A);
  and capital is within the Income Support limit.

Roles are given explicitly (is_claimant_or_partner), so the properties test
the eligibility rule rather than the role inference; the inferred case is
covered in income_support_claimant_partner_gates.yaml. Each example builds
many families in one simulation, in separate households and benefit units.
"""

import math

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

YEAR = 2025


@st.composite
def adult_inputs(draw, min_age=18):
    return {
        "age": draw(st.integers(min_age, 90)),
        "receives_carer_benefit": draw(st.booleans()),
        "care_hours": draw(st.sampled_from([0, 34, 35])),
        "esa_income_reported": draw(st.sampled_from([0, 0, 200, 3_000])),
        "esa_contrib_reported": draw(st.sampled_from([0, 0, 3_000])),
        "income_support_reported": draw(st.sampled_from([0, 1_000, 1_000])),
    }


@st.composite
def families(draw):
    """A claimant, an optional partner and up to three dependants."""
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
        dependants.append(dependant)
    eldest_dependant = max([d["age"] for d in dependants], default=0)
    adults = [draw(adult_inputs(min_age=max(18, eldest_dependant + 16)))]
    if draw(st.booleans()):
        adults.append(draw(adult_inputs()))
    for adult in adults:
        adult["is_parent"] = n_dependants > 0
    capital = {
        "income_support_assessable_capital": draw(st.sampled_from([0, 10_000, 20_000])),
        "esa_income_assessable_capital": draw(
            st.sampled_from([0, 6_250, 10_000, 20_000])
        ),
    }
    return adults, dependants, capital


@st.composite
def excluded_members(draw):
    """An adult who is neither claimant, partner nor a dependant.

    They are not in education, so a 16 to 19 year old is not a qualifying
    young person.
    """
    return {
        **draw(adult_inputs(min_age=16)),
        "current_education": "NOT_IN_EDUCATION",
    }


def situation(units):
    people, benunits, households = {}, {}, {}
    for i, (adults, dependants, capital, extra) in enumerate(units):
        members = [(m, True) for m in adults] + [(m, False) for m in dependants]
        if extra is not None:
            members.append((extra, False))
        names = []
        for j, (inputs, claimant_or_partner) in enumerate(members):
            name = f"p{i}_{j}"
            people[name] = {k: {YEAR: v} for k, v in inputs.items()}
            people[name]["is_claimant_or_partner"] = {YEAR: claimant_or_partner}
            names.append(name)
        benunits[f"b{i}"] = {
            "members": names,
            **{k: {YEAR: v} for k, v in capital.items()},
        }
        households[f"h{i}"] = {"members": names}
    return {"people": people, "benunits": benunits, "households": households}


SETTINGS = settings(
    max_examples=12,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)


@SETTINGS
@given(st.lists(st.tuples(families(), excluded_members()), min_size=1, max_size=8))
def test_excluded_member_never_changes_is_eligibility(drawn):
    without = [(*family, None) for family, _ in drawn]
    with_extra = [(*family, extra) for family, extra in drawn]
    sim = Simulation(situation=situation(without + with_extra))
    eligible = sim.calculate("income_support_eligible", YEAR)
    flags = sim.calculate("is_claimant_or_partner", YEAR)
    dependant = sim.calculate("is_child_or_young_person_for_legacy_benefits", YEAR)
    sizes = [len(a) + len(d) + (e is not None) for a, d, _, e in without + with_extra]
    ends = np.cumsum(sizes)
    k = len(drawn)
    for i in range(k):
        # The added member is the last of its benefit unit: neither claimant,
        # partner nor a dependant.
        last = ends[k + i] - 1
        assert not flags[last] and not dependant[last], drawn[i]
        assert eligible[i] == eligible[k + i], drawn[i]


def reference_eligibility(adults, dependants, capital, sp_age, parameters):
    """SSCBA 1992 s.124(1) as the model abstracts it, read family by family."""
    IS = parameters.gov.dwp.income_support
    ESA = parameters.gov.dwp.ESA.income.capital
    child_ages = [d["age"] for d in dependants if d["age"] < 16]
    lone_parent_with_young_child = (
        len(adults) == 1
        and len(dependants) > 0
        and min(child_ages, default=math.inf)
        <= IS.eligibility.lone_parent_youngest_child_age_limit
    )

    def could_claim(adult, over_qualifying_age):
        carer = adult["receives_carer_benefit"] or adult["care_hours"] >= 35
        return (
            (carer or lone_parent_with_young_child)
            and not over_qualifying_age
            and adult["esa_contrib_reported"] == 0
        )

    reported_esa = sum(a["esa_income_reported"] for a in adults)
    esa_capital = capital["esa_income_assessable_capital"]
    tariff = (
        math.ceil(
            max(0, esa_capital - ESA.tariff_income.threshold) / ESA.tariff_income.step
        )
        * ESA.tariff_income.amount
        * 52
    )
    income_related_esa = (
        reported_esa > 0 and esa_capital <= ESA.limit and reported_esa > tariff
    )
    return (
        any(could_claim(a, s) for a, s in zip(adults, sp_age))
        and not income_related_esa
        and any(a["income_support_reported"] > 0 for a in adults)
        and capital["income_support_assessable_capital"] <= IS.means_test.capital.limit
    )


@SETTINGS
@given(st.lists(st.tuples(families(), excluded_members()), min_size=1, max_size=8))
def test_is_eligibility_matches_a_direct_reading_of_s124(drawn):
    units = [(*family, extra) for family, extra in drawn]
    sim = Simulation(situation=situation(units))
    eligible = sim.calculate("income_support_eligible", YEAR)
    sp_age = sim.calculate("is_SP_age", YEAR)
    parameters = sim.tax_benefit_system.parameters(YEAR)
    start = 0
    for i, (adults, dependants, capital, extra) in enumerate(units):
        expected = reference_eligibility(
            adults,
            dependants,
            capital,
            sp_age[start : start + len(adults)],
            parameters,
        )
        assert eligible[i] == expected, units[i]
        start += len(adults) + len(dependants) + 1
