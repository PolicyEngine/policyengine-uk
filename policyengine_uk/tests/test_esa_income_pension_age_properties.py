"""Income-related ESA is never paid where pensionable age or Pension Credit bars it.

Welfare Reform Act 2007 s.1(3)(c) bars ESA for a claimant who has reached
pensionable age, their own State Pension age (s.1(6)). Sch 1 para 6(1)(c) and
(d) bar the income-related allowance where the claimant, or the other member
of the couple, is entitled to State Pension Credit. The model takes the couple
to be entitled where it meets the Pension Credit age conditions and would
claim it (meets_pension_credit_age_conditions and would_claim_pc), as Income
Support does for SSCBA 1992 s.124(1)(g). For every family drawn here:

- no family gets both: where the model pays the couple Pension Credit, or
  takes it to be on Pension Credit, the couple's income-related ESA
  (claimant_or_partner_esa_income) is nil;
- nobody who has reached pensionable age is on income-related ESA
  (is_on_income_related_esa), and a family whose every report comes from such
  a member gets none (esa_income);
- esa_income_eligible equals the family-by-family reading of the law in
  legacy_award_work_reference (esa_screen), given the model's pensionable age
  (is_SP_age) and Pension Credit proxy, so the bars combine with the work and
  capital tests as the law sets them;
- claiming Pension Credit never raises income-related ESA: the same families
  with would_claim_pc false get at least as much, and exactly as much where
  the couple does not meet the Pension Credit age conditions.

The years are 2016, when a man born before 6 December 1953 could be over the
qualifying age for State Pension Credit but under his pensionable age of 65
(Pensions Act 1995 Sch 4 para 1 rule 1), 2018, before the exclusion of
mixed-age couples (SPCA 2002 s.4(1A), from 15 May 2019), and 2026, when only
a mixed-age couple that keeps the SI 2019/37 art 4 saving
(has_mixed_age_couple_pension_credit_saving, drawn) can get Pension Credit.
Adults work some hours but have no pay, so only the other member's 24 hours
(para 6(1)(f)) and capital above £16,000 (para 6(1)(b)) bite among the older
tests; test_legacy_award_work_properties.py covers earnings. A member outside
the couple claims in their own right: the couple's Pension Credit does not bar
them, and pensionable age does. Everyone is a legacy claimant (would_claim_uc
false). Roles are given explicitly (is_claimant_or_partner). Each example
builds many families in one simulation, in separate benefit units.
"""

import numpy as np
from hypothesis import HealthCheck, event, example, given, settings
from hypothesis import strategies as st

from legacy_award_work_reference import esa_screen
from policyengine_uk import Simulation

YEARS = [2016, 2018, 2026]
# Either side of the State Pension Credit qualifying age and of pensionable
# age in each year drawn, including men aged 62 to 64 in 2016.
AGES = [30, 45, 58, 60, 61, 62, 63, 64, 65, 66, 67, 68, 70, 75, 82]
# 0 and 24 hours a week.
HOURS = [0, 0, 0, 1_248]


@st.composite
def adults(draw, outside=False):
    adult = {
        "age": draw(st.sampled_from(AGES)),
        "months_since_last_birthday": draw(st.sampled_from([0, 3, 8, 11])),
        "gender": draw(st.sampled_from(["MALE", "FEMALE"])),
        "esa_income_reported": draw(st.sampled_from([0, 3_000, 3_000])),
        "hours_worked": draw(st.sampled_from(HOURS)),
    }
    if outside:
        adult["current_education"] = "NOT_IN_EDUCATION"
    return adult


@st.composite
def families(draw):
    """A claimant, an optional partner, an optional member outside the couple,
    capital and the couple's saving and Pension Credit take-up."""
    couple = [draw(adults())]
    if draw(st.booleans()):
        couple.append(draw(adults()))
    others = [draw(adults(outside=True))] if draw(st.integers(0, 3)) == 0 else []
    benunit = {
        "esa_income_assessable_capital": draw(st.sampled_from([0, 0, 0, 20_000])),
        "has_mixed_age_couple_pension_credit_saving": draw(st.booleans()),
        "would_claim_pc": draw(st.sampled_from([True, True, False])),
    }
    return couple, others, benunit


def situation(units, year):
    people, benunits, households = {}, {}, {}
    for i, (couple, others, benunit) in enumerate(units):
        names = []
        for j, (inputs, claimant_or_partner) in enumerate(
            [(m, True) for m in couple] + [(m, False) for m in others]
        ):
            name = f"p{i}_{j}"
            people[name] = {k: {year: v} for k, v in inputs.items()}
            people[name]["is_claimant_or_partner"] = {year: claimant_or_partner}
            names.append(name)
        benunits[f"b{i}"] = {
            "members": names,
            "would_claim_uc": {year: False},
            **{k: {year: v} for k, v in benunit.items()},
        }
        households[f"h{i}"] = {"members": names}
    return {"people": people, "benunits": benunits, "households": households}


def label(units, year):
    event(f"year {year}")
    for couple, others, _ in units:
        if len(couple) == 2:
            event("couple")
        if others:
            event("member outside the couple")


NO_REPORT = {"months_since_last_birthday": 0, "esa_income_reported": 0}
# A member outside the couple who reports income-related ESA beside a
# single claimant aged 70 on Pension Credit, and one aged 70 themselves.
OUTSIDE_REPORTERS = [
    (
        [{"age": 70, "gender": "FEMALE", "hours_worked": 0, **NO_REPORT}],
        [
            {
                "age": age,
                "months_since_last_birthday": 0,
                "gender": "MALE",
                "esa_income_reported": 3_000,
                "hours_worked": 0,
                "current_education": "NOT_IN_EDUCATION",
            }
        ],
        {
            "esa_income_assessable_capital": 0,
            "has_mixed_age_couple_pension_credit_saving": False,
            "would_claim_pc": True,
        },
    )
    for age in [40, 70]
]


SETTINGS = settings(
    max_examples=12,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
FAMILIES = st.lists(families(), min_size=1, max_size=8)


@SETTINGS
@given(FAMILIES, st.sampled_from(YEARS))
def test_no_family_gets_pension_credit_and_income_related_esa(units, year):
    label(units, year)
    sim = Simulation(situation=situation(units, year))
    pension_credit = sim.calculate("pension_credit", year)
    on_pension_credit = sim.calculate(
        "meets_pension_credit_age_conditions", year
    ) & sim.calculate("would_claim_pc", year)
    couple_esa = sim.calculate("claimant_or_partner_esa_income", year)
    if (on_pension_credit & (couple_esa == 0)).any():
        event("a couple on Pension Credit")
    if (~on_pension_credit & (couple_esa > 0)).any():
        event("a couple paid income-related ESA")
    # Pension Credit is paid only on the Pension Credit route, to a family
    # that would claim it (is_pension_credit_eligible, pension_credit).
    assert not ((pension_credit > 0) & ~on_pension_credit).any()
    # Para 6(1)(c) and (d).
    assert (couple_esa[on_pension_credit] == 0).all(), units
    assert not ((pension_credit > 0) & (couple_esa > 0)).any(), units


@SETTINGS
@given(FAMILIES, st.sampled_from(YEARS))
@example(OUTSIDE_REPORTERS, 2026)
def test_nobody_over_pensionable_age_is_on_income_related_esa(units, year):
    label(units, year)
    sim = Simulation(situation=situation(units, year))
    pensionable_age = sim.calculate("is_SP_age", year)
    on_esa = sim.calculate("is_on_income_related_esa", year)
    esa = sim.calculate("esa_income", year)
    if (pensionable_age & ~on_esa).any():
        event("someone over pensionable age")
    # s.1(3)(c): the award is not payable to them.
    assert not (pensionable_age & on_esa).any(), units
    start = 0
    for i, (couple, others, _) in enumerate(units):
        members = couple + others
        flags = pensionable_age[start : start + len(members)]
        reporters = [m["esa_income_reported"] > 0 for m in members]
        if any(reporters) and all(f for f, r in zip(flags, reporters) if r):
            event("every report from someone over pensionable age")
            assert esa[i] == 0, units[i]
        start += len(members)


@SETTINGS
@given(FAMILIES, st.sampled_from(YEARS))
@example(OUTSIDE_REPORTERS[:1], 2026)
@example(OUTSIDE_REPORTERS[1:], 2026)
def test_screen_matches_a_family_by_family_reading(units, year):
    label(units, year)
    sim = Simulation(situation=situation(units, year))
    eligible = sim.calculate("esa_income_eligible", year)
    pensionable_age = sim.calculate("is_SP_age", year)
    on_pension_credit = sim.calculate(
        "meets_pension_credit_age_conditions", year
    ) & sim.calculate("would_claim_pc", year)
    parameters = sim.tax_benefit_system.parameters(year)
    if eligible.any():
        event("some screen passes")
    start = 0
    for i, (couple, others, benunit) in enumerate(units):
        members = [
            dict(member, is_SP_age=pensionable_age[start + j])
            for j, member in enumerate(couple + others)
        ]
        expected = esa_screen(
            members[: len(couple)],
            members[len(couple) :],
            benunit["esa_income_assessable_capital"],
            parameters,
            on_pension_credit=on_pension_credit[i],
        )
        assert eligible[i] == expected, (year, units[i])
        start += len(members)


@SETTINGS
@given(FAMILIES, st.sampled_from(YEARS))
@example(OUTSIDE_REPORTERS, 2026)
def test_claiming_pension_credit_never_raises_income_related_esa(units, year):
    label(units, year)
    n = len(units)

    def claiming(claims):
        return [
            (couple, others, dict(benunit, would_claim_pc=claims))
            for couple, others, benunit in units
        ]

    sim = Simulation(situation=situation(claiming(True) + claiming(False), year))
    esa = sim.calculate("esa_income", year)
    route = sim.calculate("meets_pension_credit_age_conditions", year)
    assert (route[:n] == route[n:]).all()
    if (esa[n:] > esa[:n]).any():
        event("claiming Pension Credit ended an award")
    assert (esa[:n] <= esa[n:] + 0.01).all(), units
    assert np.allclose(esa[:n][~route[:n]], esa[n:][~route[:n]], atol=0.01), units
