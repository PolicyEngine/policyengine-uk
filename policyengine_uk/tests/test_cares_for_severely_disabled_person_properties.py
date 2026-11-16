"""Carer benefits pay on caring hours only for care of a severely disabled
person.

The Department for Work and Pensions pays Carer's Allowance only for caring
for a "severely disabled person" (SSCBA 1992 s.70(1)), defined by the benefit
payable for them (s.70(2)). Social Security Scotland pays Carer Support
Payment only for care of a person "to whom a qualifying disability benefit is
normally payable" (SSI 2023/302 reg 5(1)). DWP includes the Universal Credit
carer element (UC Regs 2013 reg 29) for a claimant who meets the Carer's
Allowance conditions, or would but for the earnings limit or living in
Scotland (reg 30(1)(a)). The input cares_for_severely_disabled_person records
whether the person cared for gets such a benefit. It defaults to true, and
the model reads it only on the route through caring hours: a reported award
(carers_allowance_reported) still counts.

Invariants, for benefit units of one or two adults and up to one qualifying
young person, each with drawn caring hours, reported award, take-up,
earnings and overlapping benefit, in each country, in 2024 (Scotland still on
Carer's Allowance), 2026, 2030 (the year the Carer's Allowance earnings
taper starts) and 2031, where no input supplies a carer benefit amount or
entitlement:

1. leaving the input out gives exactly the values that setting it true
   gives, for carers_allowance, carer_support_payment, is_carer_for_benefits,
   is_entitled_to_carer_benefit, uc_carer_element,
   partners_care_for_same_severely_disabled_person and
   carer_minimum_guarantee_addition;
2. setting one person's input false never raises that person's
   carers_allowance or carer_support_payment and never turns that person's
   is_carer_for_benefits or is_entitled_to_carer_benefit on; it never raises
   the benefit unit's uc_carer_element or carer_minimum_guarantee_addition,
   and never turns partners_care_for_same_severely_disabled_person on;
3. before the taper, setting every person's input false never raises any
   person's carers_allowance or carer_support_payment, or the benefit unit's
   amounts, and never turns any of those flags on;
4. a person whose input is false and who has no reported award gets no
   Carer's Allowance or Carer Support Payment, before or after the
   overlapping-benefit adjustment, and is neither entitled to a carer benefit
   nor a carer for benefits;
5. setting the input false for the people with a reported award leaves every
   person's carers_allowance and carer_support_payment as they were, and
   every person's is_carer_for_benefits too, except for a reported recipient
   who would not claim, whose route through caring hours the input closes.

And for couples where an input supplies each partner's entitlement to a
carer benefit, true or false:

6. partners_care_for_same_severely_disabled_person is false exactly where
   both partners have an entitlement and an award: a reported award, or an
   entitlement that caring hours for a severely disabled person don't explain
   (fewer than the minimum hours, the input false, or no claim). Leaving the
   input out gives what setting it true gives, and setting inputs false never
   turns the flag on.

Only one of two partners who care for the same person can have the award
(SSCBA 1992 s.70(7ZA); SSI 2023/302 reg 5(3)). So when one partner's input
goes false, the model can give the award to the other partner, whose amount
and entitlement then rise, as the law has it; the second invariant therefore
compares only the person whose input changes, and the benefit unit. Under
the earnings taper the partners' awards can differ, and the model gives the
award to the partner with the larger one: setting both inputs false can then
give the other partner back a reported award, so the third invariant holds
only before the taper. Two fixed tests at the end run both cases.

The first five invariants need households where no input supplies a carer
benefit entitlement or amount. Without one, the input can't change
partners_care_for_same_severely_disabled_person, so the sixth invariant
supplies the entitlements. A supplied entitlement that caring hours no longer
explain counts as a second award: it can turn that flag false and give the
couple a second carer premium or Universal Credit carer element, as the YAML
case "A supplied entitlement whose caring hours go to someone not severely
disabled counts as a second award" shows. Batching needs the same care:
supplying a value for one person makes it an input for every person in the
simulation, so the others take its default, not the formula. The sixth
invariant's households supply the entitlement for every person.

Tests 1, 2, 3, 5 and 6 build each benefit unit more than once in one
simulation, in separate households: as drawn, and with the input changed.
Test 4 builds each unit once, with each member's input false or left out.
"""

import numpy as np
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

INPUT = "cares_for_severely_disabled_person"
YEARS = [2024, 2026, 2030, 2031]
YEARS_BEFORE_TAPER = [2024, 2026]
COUNTRIES = ["ENGLAND", "SCOTLAND", "WALES", "NORTHERN_IRELAND"]
AWARD = 4_000
# Annual amounts are float32; a change smaller than half a penny is not one.
TOLERANCE = 0.005

PERSON_AMOUNTS = ["carers_allowance", "carer_support_payment"]
PERSON_FLAGS = ["is_carer_for_benefits", "is_entitled_to_carer_benefit"]
BENUNIT_AMOUNTS = ["uc_carer_element", "carer_minimum_guarantee_addition"]
BENUNIT_FLAGS = ["partners_care_for_same_severely_disabled_person"]
PRE_OVERLAP = ["carers_allowance_pre_overlap", "carer_support_payment_pre_overlap"]


@st.composite
def carer_inputs(draw, earns=True):
    # The draws lean towards a claim within the earnings limit, so that most
    # carers who care the hours have an award the input can take away.
    return {
        # Either side of the 35-hour minimum both benefits use.
        "care_hours": draw(st.sampled_from([0, 20, 34, 35, 40, 40, 60])),
        "carers_allowance_reported": draw(st.sampled_from([0, 0, AWARD])),
        "would_claim_carers_allowance": draw(st.sampled_from([True, True, False])),
        # From 2026: below the earnings limit, above it by less than the rate
        # (13,500 exceeds it by 50.60 a week in 2026 and 21.70 in 2031, so the
        # taper pays some allowance), and far above it. The lower 2024 limit
        # puts 8,000 and 13,500 above it, by 2.84 and 103.60 a week.
        "employment_income": (
            draw(st.sampled_from([0, 0, 0, 8_000, 13_500, 30_000])) if earns else 0
        ),
        # Above the carer rates, so an overlapping benefit can reduce the
        # payment to nil and leave the entitlement.
        "incapacity_benefit_reported": draw(st.sampled_from([0, 0, 6_000])),
    }


@st.composite
def benefit_units(draw):
    """One benefit unit in its own household: its members, the country, one
    member whose input a test changes, and for each member the input false
    or left out (None)."""
    has_young_person = draw(st.booleans())
    young_person_age = draw(st.integers(16, 19))
    head_age = draw(st.integers(young_person_age + 16 if has_young_person else 18, 85))
    members = [{"age": head_age, "is_parent": has_young_person, **draw(carer_inputs())}]
    if draw(st.booleans()):
        # Within 15 years of the head in both directions when either could be
        # under 20, and under 20 years older otherwise, so the model reads
        # neither as the other's child.
        oldest_partner = min(85, head_age + 19) if head_age >= 20 else head_age + 15
        youngest_partner = max(18, head_age - 15)
        if has_young_person:
            youngest_partner = max(youngest_partner, young_person_age + 16)
        members.append(
            {
                "age": draw(st.integers(youngest_partner, oldest_partner)),
                "is_parent": has_young_person,
                **draw(carer_inputs()),
            }
        )
    adults = len(members)
    if has_young_person:
        # A qualifying young person: 16 to 19 in non-advanced education.
        members.append(
            {
                "age": young_person_age,
                "current_education": "UPPER_SECONDARY",
                **draw(carer_inputs(earns=False)),
            }
        )
    return {
        "members": members,
        "adults": adults,
        "country": draw(st.sampled_from(COUNTRIES)),
        "chosen": draw(st.integers(0, len(members) - 1)),
        "inputs": [draw(st.sampled_from([False, None])) for _ in members],
    }


def with_input(unit, values):
    """The unit with the input set to each member's value, or left out where
    the value is None."""
    members = [
        member if value is None else {**member, INPUT: value}
        for member, value in zip(unit["members"], values)
    ]
    return {**unit, "members": members}


@st.composite
def couples_with_supplied_entitlements(draw):
    """A couple in its own household, where an input supplies each partner's
    entitlement to a carer benefit, true or false, and each partner's input
    is false or left out (None)."""
    head_age = draw(st.integers(18, 85))
    oldest_partner = min(85, head_age + 19) if head_age >= 20 else head_age + 15
    ages = [head_age, draw(st.integers(max(18, head_age - 15), oldest_partner))]
    members = [
        {
            "age": age,
            "is_parent": False,
            "is_entitled_to_carer_benefit": draw(st.booleans()),
            **draw(carer_inputs()),
        }
        for age in ages
    ]
    return {
        "members": members,
        "adults": 2,
        "country": draw(st.sampled_from(COUNTRIES)),
        "chosen": draw(st.integers(0, 1)),
        "inputs": [draw(st.sampled_from([False, None])) for _ in members],
    }


def simulate(units, year):
    people, benunits, households = {}, {}, {}
    for i, unit in enumerate(units):
        names = []
        for j, inputs in enumerate(unit["members"]):
            name = f"p{i}_{j}"
            people[name] = {key: {year: value} for key, value in inputs.items()}
            names.append(name)
        benunits[f"b{i}"] = {"members": names}
        households[f"h{i}"] = {"members": names, "country": {year: unit["country"]}}
    sim = Simulation(
        situation={"people": people, "benunits": benunits, "households": households}
    )
    offsets = np.cumsum([0] + [len(unit["members"]) for unit in units])
    return sim, offsets


def calculate(units, year, variables):
    sim, offsets = simulate(units, year)
    values = {name: sim.calculate(name, year) for name in variables}
    return values, offsets


SETTINGS = settings(
    max_examples=12,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)

UNITS = st.lists(benefit_units(), min_size=1, max_size=6)

ADULT = {
    "is_parent": False,
    "carers_allowance_reported": 0,
    "would_claim_carers_allowance": True,
    "employment_income": 0,
    "incapacity_benefit_reported": 0,
}
# Both partners care 40 hours a week. The elder, the benefit unit head, has the
# couple's one award; with the elder's input false the younger has it.
COUPLE = {
    "members": [
        {**ADULT, "age": 40, "care_hours": 40},
        {**ADULT, "age": 38, "care_hours": 40},
    ],
    "adults": 2,
    "country": "ENGLAND",
    "chosen": 0,
    "inputs": [False, None],
}
# The same couple, aged 70 and 60, where an overlapping benefit takes the
# elder's award to nil: with the elder's input false, the younger is paid.
OVERLAPPED_COUPLE = {
    **COUPLE,
    "members": [
        {**ADULT, "age": 70, "care_hours": 40, "incapacity_benefit_reported": 6_000},
        {**ADULT, "age": 60, "care_hours": 40},
    ],
}
# Under the taper: the elder's reported award, tapered by earnings, loses to
# the younger's larger award on caring hours. With both inputs false the elder
# has it back; with only the elder's false, nothing changes.
TAPERED_COUPLE = {
    **COUPLE,
    "members": [
        {
            **ADULT,
            "age": 40,
            "care_hours": 40,
            "carers_allowance_reported": AWARD,
            "employment_income": 13_500,
        },
        {**ADULT, "age": 38, "care_hours": 40},
    ],
    "inputs": [False, False],
}
SCOTTISH_COUPLE = {**COUPLE, "country": "SCOTLAND"}
# The elder has a reported award; the younger cares 40 hours a week for
# someone not severely disabled. Each has a supplied entitlement, so the
# younger's counts as a second award once the input says the hours don't
# explain it.
SUPPLIED_COUPLE = {
    **COUPLE,
    "members": [
        {
            **ADULT,
            "age": 40,
            "care_hours": 40,
            "carers_allowance_reported": AWARD,
            "is_entitled_to_carer_benefit": True,
        },
        {**ADULT, "age": 38, "care_hours": 40, "is_entitled_to_carer_benefit": True},
    ],
    "chosen": 1,
    "inputs": [None, False],
}


@SETTINGS
@given(UNITS, st.sampled_from(YEARS))
@example(drawn=[COUPLE, SCOTTISH_COUPLE], year=2026)
def test_input_left_out_matches_input_true(drawn, year):
    variables = PERSON_AMOUNTS + PERSON_FLAGS + ["is_claimant_or_partner"]
    benunit_variables = BENUNIT_AMOUNTS + BENUNIT_FLAGS
    true = [with_input(unit, [True] * len(unit["members"])) for unit in drawn]
    values, offsets = calculate(drawn + true, year, variables + benunit_variables)
    k = len(drawn)
    n = offsets[k]
    for i, unit in enumerate(drawn):
        # The generator's construction, checked against the model: the
        # adults are the claimant and partner, the young person is not.
        flags = values["is_claimant_or_partner"][offsets[i] : offsets[i + 1]]
        adults = unit["adults"]
        assert flags[:adults].all() and not flags[adults:].any(), unit
    for name in variables:
        assert np.array_equal(values[name][:n], values[name][n:]), name
    for name in benunit_variables:
        assert np.array_equal(values[name][:k], values[name][k:]), name


@SETTINGS
@given(UNITS, st.sampled_from(YEARS))
@example(drawn=[COUPLE, OVERLAPPED_COUPLE, SCOTTISH_COUPLE], year=2026)
@example(drawn=[TAPERED_COUPLE], year=2031)
def test_one_persons_input_false_never_raises_their_award(drawn, year):
    changed = [
        with_input(
            unit,
            [
                False if j == unit["chosen"] else None
                for j in range(len(unit["members"]))
            ],
        )
        for unit in drawn
    ]
    variables = PERSON_AMOUNTS + PERSON_FLAGS + BENUNIT_AMOUNTS + BENUNIT_FLAGS
    values, offsets = calculate(drawn + changed, year, variables)
    k = len(drawn)
    for i, unit in enumerate(drawn):
        before = offsets[i] + unit["chosen"]
        after = offsets[k + i] + unit["chosen"]
        for name in PERSON_AMOUNTS:
            assert values[name][after] <= values[name][before] + TOLERANCE, (name, unit)
        for name in PERSON_FLAGS:
            assert values[name][before] or not values[name][after], (name, unit)
        for name in BENUNIT_AMOUNTS:
            assert values[name][k + i] <= values[name][i] + TOLERANCE, (name, unit)
        for name in BENUNIT_FLAGS:
            assert values[name][i] or not values[name][k + i], (name, unit)


@SETTINGS
@given(UNITS, st.sampled_from(YEARS_BEFORE_TAPER))
@example(drawn=[COUPLE, OVERLAPPED_COUPLE, SCOTTISH_COUPLE], year=2026)
def test_everyones_input_false_never_raises_an_award_before_the_taper(drawn, year):
    false = [with_input(unit, [False] * len(unit["members"])) for unit in drawn]
    variables = PERSON_AMOUNTS + PERSON_FLAGS + BENUNIT_AMOUNTS + BENUNIT_FLAGS
    values, offsets = calculate(drawn + false, year, variables)
    k = len(drawn)
    n = offsets[k]
    for name in PERSON_AMOUNTS:
        assert (values[name][n:] <= values[name][:n] + TOLERANCE).all(), name
    for name in PERSON_FLAGS:
        assert not (values[name][n:] & ~values[name][:n]).any(), name
    for name in BENUNIT_AMOUNTS:
        assert (values[name][k:] <= values[name][:k] + TOLERANCE).all(), name
    for name in BENUNIT_FLAGS:
        assert not (values[name][k:] & ~values[name][:k]).any(), name


@SETTINGS
@given(UNITS, st.sampled_from(YEARS))
@example(drawn=[COUPLE, TAPERED_COUPLE, SCOTTISH_COUPLE], year=2031)
def test_input_false_without_a_reported_award_pays_no_carer_benefit(drawn, year):
    units = [with_input(unit, unit["inputs"]) for unit in drawn]
    variables = PERSON_AMOUNTS + PRE_OVERLAP + PERSON_FLAGS
    values, offsets = calculate(units, year, variables)
    for i, unit in enumerate(drawn):
        for j, (member, value) in enumerate(zip(unit["members"], unit["inputs"])):
            if value is False and member["carers_allowance_reported"] == 0:
                for name in PERSON_AMOUNTS + PRE_OVERLAP:
                    assert values[name][offsets[i] + j] == 0, (name, unit)
                for name in PERSON_FLAGS:
                    assert not values[name][offsets[i] + j], (name, unit)


@SETTINGS
@given(UNITS, st.sampled_from(YEARS))
@example(drawn=[TAPERED_COUPLE], year=2031)
@example(drawn=[{**COUPLE, "members": TAPERED_COUPLE["members"]}], year=2026)
def test_reported_award_pays_the_same_whatever_the_input(drawn, year):
    toggled = [
        with_input(
            unit,
            [
                False if member["carers_allowance_reported"] > 0 else None
                for member in unit["members"]
            ],
        )
        for unit in drawn
    ]
    variables = PERSON_AMOUNTS + ["is_carer_for_benefits"]
    values, offsets = calculate(drawn + toggled, year, variables)
    n = offsets[len(drawn)]
    for name in PERSON_AMOUNTS:
        assert np.array_equal(values[name][:n], values[name][n:]), name
    # A reported award the person would claim keeps them a carer for benefits
    # whatever the input says, as the reported limb of is_carer_for_benefits
    # has it; a reported recipient who would not claim relies on the hours.
    claims = np.array(
        [
            member["carers_allowance_reported"] == 0
            or member["would_claim_carers_allowance"]
            for unit in drawn
            for member in unit["members"]
        ]
    )
    carer = values["is_carer_for_benefits"]
    assert np.array_equal(carer[:n][claims], carer[n:][claims])


@SETTINGS
@given(
    st.lists(couples_with_supplied_entitlements(), min_size=1, max_size=6),
    st.sampled_from(YEARS),
)
@example(drawn=[SUPPLIED_COUPLE, {**SUPPLIED_COUPLE, "country": "SCOTLAND"}], year=2026)
def test_a_supplied_entitlement_counts_as_an_award_unless_hours_explain_it(drawn, year):
    true = [with_input(unit, [True, True]) for unit in drawn]
    changed = [with_input(unit, unit["inputs"]) for unit in drawn]
    sim, offsets = simulate(drawn + true + changed, year)
    same = sim.calculate("partners_care_for_same_severely_disabled_person", year)
    claimant_or_partner = sim.calculate("is_claimant_or_partner", year)
    gov = sim.tax_benefit_system.parameters(year).gov
    k = len(drawn)
    assert claimant_or_partner.all()
    for i, unit in enumerate(drawn):
        assert same[k + i] == same[i], unit
        assert same[i] or not same[2 * k + i], unit
        # The minimum hours of the benefit that applies: Carer Support
        # Payment's in Scotland from 2025, Carer's Allowance's otherwise.
        if unit["country"] == "SCOTLAND" and year >= 2025:
            min_hours = gov.social_security_scotland.carer_support_payment.min_hours
        else:
            min_hours = gov.dwp.carers_allowance.min_hours
        awards = 0
        for member, value in zip(unit["members"], unit["inputs"]):
            explained = (
                member["care_hours"] >= min_hours
                and value is not False
                and member["would_claim_carers_allowance"]
            )
            reported = member["carers_allowance_reported"] > 0
            awards += member["is_entitled_to_carer_benefit"] and (
                reported or not explained
            )
        assert same[2 * k + i] == (awards < 2), unit


def _couple_values(units, year, variables):
    values, _ = calculate(units, year, variables)
    return {name: [round(float(x), 2) for x in values[name]] for name in variables}


def test_award_passes_to_the_partner_who_cares_for_a_severely_disabled_person():
    # The cases that the second invariant leaves out, run as they are. With
    # the elder's input false the younger's allowance rises from nil to the
    # full rate, 86.45 * 52 = 4,495.40: one partner's hours no longer count,
    # so the other is the only one caring for a severely disabled person.
    names = ["carers_allowance", "is_entitled_to_carer_benefit"]
    default = _couple_values([COUPLE], 2026, names)
    changed = _couple_values([with_input(COUPLE, COUPLE["inputs"])], 2026, names)
    assert default == {
        "carers_allowance": [4_495.4, 0],
        "is_entitled_to_carer_benefit": [1, 0],
    }
    assert changed == {
        "carers_allowance": [0, 4_495.4],
        "is_entitled_to_carer_benefit": [0, 1],
    }
    # Where an overlapping benefit takes the elder's award to nil, the couple
    # had nothing and now has the younger's full allowance.
    overlapped = _couple_values([OVERLAPPED_COUPLE], 2026, names)
    changed = _couple_values(
        [with_input(OVERLAPPED_COUPLE, OVERLAPPED_COUPLE["inputs"])], 2026, names
    )
    assert overlapped["carers_allowance"] == [0, 0]
    assert changed["carers_allowance"] == [0, 4_495.4]


def test_under_the_taper_both_inputs_false_can_give_back_a_reported_award():
    # The case that the third invariant leaves out. In 2031 the elder's
    # tapered award falls short of the younger's award on caring hours, so
    # the model gives the younger the couple's award. With both inputs false
    # the younger has none, and the elder keeps the reported award.
    names = ["carers_allowance_pre_couple_limit", "carers_allowance"]
    default = _couple_values([TAPERED_COUPLE], 2031, names)
    both_false = _couple_values(
        [with_input(TAPERED_COUPLE, TAPERED_COUPLE["inputs"])], 2031, names
    )
    elder_award, younger_award = default["carers_allowance_pre_couple_limit"]
    assert 0 < elder_award < younger_award
    assert default["carers_allowance"] == [0, younger_award]
    assert both_false["carers_allowance"] == [elder_award, 0]
