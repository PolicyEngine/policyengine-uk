"""The legacy carer premium and the Income Support carer route follow only the
claimant and partner.

IS Regs 1987 Sch 2 para 14ZA(1) (and the JSA, ESA, HB and CTR equivalents)
give the carer premium where "the claimant or his partner is, or both of them
are" entitled to Carer's Allowance or Carer Support Payment, and para 15(7)
pays it "in respect of each person who satisfied the condition". Two people
caring for the same severely disabled person cannot both be entitled (SSCBA
s.70(7ZA); SSI 2023/302 reg 5(3)). The Income Support carer route (Sch 1B
para 4, reg 4ZA, SSCBA s.124(1)(e)) likewise needs the claimant to be the
carer. No new claim for Income Support can be made (UC (Transitional
Provisions) Regs 2014 reg 6A(1)) and a partner who takes over an award does
so by claiming (Claims and Payments Regs 1987 reg 4(4)), so the claimant is
whichever of the claimant and partner holds the existing award.

Invariants, for any family of a claimant, an optional partner and up to three
dependent children or qualifying young persons:

- a dependant's caring never changes carer_premium or income_support_eligible;
- carer_premium is the per-person amount, weekly x 52, times the number of
  claimants and partners entitled to a carer benefit
  (is_entitled_to_carer_benefit, which keeps an allowance reduced to nil by
  an overlapping benefit and excludes caring hours without a claim), capped
  at one when they are treated as caring for the same person; it is 0, one
  amount or two;
- unless supplied, partners are treated as caring for the same person unless
  both are entitled with a reported Carer's Allowance award (these families
  supply no allowance amounts, pre-overlap amounts or entitlements directly,
  the model's other kind of award);
- supplying "same person" never raises the premium and caps it at one amount;
- caring by the claimant or partner never removes Income Support eligibility
  or lowers the premium, and below pension age it always opens the IS route
  when the one who cares holds the Income Support award.

Adults are 18 to 85, so pension-age families are covered. No adult under 20
is 16 or more years younger than the other adult, whom the model would then
presume to be their parent.

Each example builds every family twice in one simulation, in separate
households and benefit units: once as drawn and once with a changed caring
pattern.
"""

import numpy as np
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st
from policyengine_core.reforms import Reform

from policyengine_uk import Simulation

YEAR = 2026
WEEKS = 52
AWARD = 4_000
CA_HOURS = 35


@st.composite
def carer_inputs(draw):
    # Either route to Carer's Allowance entitlement in the model: a reported
    # award, or the qualifying hours of care, each only for someone who would
    # claim. Hours without a claim still make a carer for benefits.
    return {
        "carers_allowance_reported": draw(st.sampled_from([0, AWARD])),
        "care_hours": draw(st.sampled_from([0, 20, 34, 35, 50])),
        "would_claim_carers_allowance": draw(st.booleans()),
    }


# Above the Carer's Allowance rate, so an overlapping incapacity benefit
# reduces the allowance to nil and leaves the entitlement.
OVERLAPPING = st.sampled_from([0, 5_000])


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
    eldest_dependant = max([d["age"] for d in dependants], default=0)
    head_age = draw(st.integers(max(18, eldest_dependant + 16), 85))
    has_parent_flag = n_dependants > 0
    head = {
        "age": head_age,
        "is_parent": has_parent_flag,
        "income_support_reported": 1_000,
        "incapacity_benefit_reported": draw(OVERLAPPING),
        **draw(carer_inputs()),
    }
    family = [head]
    if draw(st.booleans()):
        # Within 15 years of the head in both directions when either could be
        # under 20, so neither is presumed the other's child.
        oldest_partner = 85 if head_age >= 20 else head_age + 15
        family.append(
            {
                "age": draw(st.integers(max(18, head_age - 15), oldest_partner)),
                "is_parent": has_parent_flag,
                # Sometimes both report the award, so the partner can be the
                # claimant.
                "income_support_reported": draw(st.sampled_from([0, 1_000])),
                "incapacity_benefit_reported": draw(OVERLAPPING),
                **draw(carer_inputs()),
            }
        )
    return family + dependants, len(family)


def situation(units, same_person=None):
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
        if same_person is not None:
            benunits[f"b{i}"]["partners_care_for_same_severely_disabled_person"] = {
                YEAR: bool(same_person[i])
            }
        households[f"h{i}"] = {"members": names}
    return {"people": people, "benunits": benunits, "households": households}


NOT_CARING = {"carers_allowance_reported": 0, "care_hours": 0}
CARING = {
    "carers_allowance_reported": AWARD,
    "care_hours": 35,
    "would_claim_carers_allowance": True,
}

SETTINGS = settings(
    max_examples=15,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)

# The generator's age boundary: an 18-year-old head with a partner 15 years
# older is drawn; 16 years older is not (the model would presume a child).
BOUNDARY = [
    {
        "age": 18,
        "is_parent": False,
        "income_support_reported": 1_000,
        **CARING,
    },
    {"age": 33, "is_parent": False, **CARING},
]


@SETTINGS
@given(st.lists(families(), min_size=1, max_size=6))
@example(drawn=[(BOUNDARY, 2)])
def test_dependants_caring_never_changes_premium_or_is_eligibility(drawn):
    units = [family for family, _ in drawn]
    adults = [n for _, n in drawn]
    without = [
        family[:n] + [{**member, **NOT_CARING} for member in family[n:]]
        for family, n in zip(units, adults)
    ]
    sim = Simulation(situation=situation(units + without))
    flags = sim.calculate("is_claimant_or_partner", YEAR)
    entitled = sim.calculate("is_entitled_to_carer_benefit", YEAR)
    offsets = np.cumsum([0] + [len(f) for f in units + without])
    for i, n in enumerate(adults):
        # The generator's construction, checked against the model: the first
        # n members are the claimant and partner, the rest are dependants.
        members = flags[offsets[i] : offsets[i + 1]]
        assert members[:n].all() and not members[n:].any(), units[i]
    premium = sim.calculate("carer_premium", YEAR)
    eligible = sim.calculate("income_support_eligible", YEAR)
    same_person = sim.calculate("partners_care_for_same_severely_disabled_person", YEAR)
    amount = sim.tax_benefit_system.parameters(YEAR).gov.dwp.carer_premium.single
    k = len(units)
    for i, n in enumerate(adults):
        assert abs(premium[i] - premium[k + i]) < 0.01, units[i]
        assert eligible[i] == eligible[k + i], units[i]
        adult_slice = slice(offsets[i], offsets[i] + n)
        # Entitlement from the inputs (England, the default country): a
        # reported award or the qualifying hours, for someone who would claim.
        claims = [
            member.get("would_claim_carers_allowance", True)
            and (
                member["carers_allowance_reported"] > 0
                or member["care_hours"] >= CA_HOURS
            )
            for member in units[i][:n]
        ]
        assert list(entitled[adult_slice]) == claims, units[i]
        awards = sum(
            claim and member["carers_allowance_reported"] > 0
            for claim, member in zip(claims, units[i][:n])
        )
        assert same_person[i] == (awards < 2), units[i]
        qualifying = sum(claims)
        if same_person[i]:
            qualifying = min(qualifying, 1)
        assert abs(premium[i] - qualifying * amount * WEEKS) < 0.01, units[i]
        assert 0 <= premium[i] <= 2 * amount * WEEKS + 0.01, units[i]


@SETTINGS
@given(st.lists(families(), min_size=1, max_size=6), st.data())
def test_claimant_or_partner_caring_never_removes_is_eligibility(drawn, data):
    units = [family for family, _ in drawn]
    adults = [n for _, n in drawn]
    # Make one of the claimant and partner a carer with a reported Carer's
    # Allowance award.
    with_caring = []
    holds_award = []
    for family, n in zip(units, adults):
        who = data.draw(st.integers(0, n - 1))
        # Caring opens the IS route only for the one who holds the award.
        holds_award.append(family[who].get("income_support_reported", 0) > 0)
        with_caring.append(
            [
                {**member, **CARING} if j == who else member
                for j, member in enumerate(family)
            ]
        )
    sim = Simulation(situation=situation(units + with_caring))
    eligible = sim.calculate("income_support_eligible", YEAR)
    premium = sim.calculate("carer_premium", YEAR)
    sp_age = sim.calculate("is_SP_age", YEAR)
    offsets = np.cumsum([0] + [len(f) for f in units + with_caring])
    k = len(units)
    for i in range(k):
        assert eligible[k + i] >= eligible[i], units[i]
        if holds_award[i] and not sp_age[offsets[k + i] : offsets[k + i + 1]].any():
            assert eligible[k + i], units[i]
        assert premium[k + i] >= premium[i] - 0.01, units[i]


@SETTINGS
@given(st.lists(families(), min_size=1, max_size=6))
def test_caring_for_the_same_person_pays_at_most_one_premium(drawn):
    units = [family for family, _ in drawn]
    k = len(units)
    sim = Simulation(
        situation=situation(units + units, same_person=[False] * k + [True] * k)
    )
    premium = sim.calculate("carer_premium", YEAR)
    amount = sim.tax_benefit_system.parameters(YEAR).gov.dwp.carer_premium.single
    for i in range(k):
        assert premium[k + i] <= premium[i] + 0.01, units[i]
        assert abs(premium[k + i] - min(premium[i], amount * WEEKS)) < 0.01, units[i]


def _couple_caring(country, hours, year, reform=None):
    situation = {
        "people": {
            "a": {"age": {year: 40}, "care_hours": {year: hours}},
            "b": {"age": {year: 38}, "care_hours": {year: hours}},
        },
        "benunits": {"bu": {"members": ["a", "b"]}},
        "households": {"h": {"members": ["a", "b"], "country": {year: country}}},
    }
    sim = Simulation(situation=situation, reform=reform)
    amount = sim.tax_benefit_system.parameters(year).gov.dwp.carer_premium.single
    return (
        bool(sim.calculate("partners_care_for_same_severely_disabled_person", year)[0]),
        float(sim.calculate("carer_premium", year)[0]),
        amount * WEEKS,
    )


def test_scottish_caring_hours_follow_carer_support_payment():
    # The hours that explain an entitlement in the same-person default are
    # Carer Support Payment's in Scotland from 2025 and Carer's Allowance's
    # otherwise, as in carers_allowance_pre_overlap. Raising only the Carer's
    # Allowance minimum to 40 leaves a Scottish couple who each care 36 hours
    # entitled to Carer Support Payment on hours alone, so the default treats
    # them as caring for the same person: one premium, not two.
    reform = Reform.from_dict(
        {"gov.dwp.carers_allowance.min_hours": {"2020-01-01.2030-12-31": 40}},
        country_id="uk",
    )
    same, premium, one = _couple_caring("SCOTLAND", 36, 2026, reform)
    assert same and abs(premium - one) < 0.01
    same, premium, one = _couple_caring("SCOTLAND", 36, 2026)
    assert same and abs(premium - one) < 0.01
    # Carer's Allowance applies in England, and in Scotland before 2025, so
    # 36 hours fall short of the reformed minimum and give no entitlement.
    assert _couple_caring("ENGLAND", 36, 2026, reform)[1] == 0
    assert _couple_caring("SCOTLAND", 36, 2024, reform)[1] == 0
