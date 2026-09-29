"""Property-based and differential tests for Pension Credit eligibility rules.

Invariants:

1. Savings Credit age condition (SPCA 2002 s.3(1)(a)). For every year from
   2016 to 2040, age from 16 to 100 and sex, meets_savings_credit_age_requirement
   equals a reference that walks every birth date consistent with the model's
   age convention (born 6 April Y - A to 5 April Y - A + 1) and applies the
   Pensions Act 1995 Sch. 4 para. 1 pensionable-age rules and Table 1 to each.
   The reference also checks that each window is homogeneous, which is what
   lets the model compare birth years. Before 2016 the condition is age 65.
2. Severe disability addition (SPC Regs 2002 Sch. I paras 1-2, reg. 6(5)).
   For random benefit units and households, the addition equals a reference
   truth table written from the regulation text, with the model's documented
   carer assumption, and is always 0, 1 or 2 times the weekly amount times
   52, with the double rate only for couples.
3. Qualifying young person (reg. 4A). For random 14- to 21-year-olds the
   model equals the reg. 4A text.
4. Mixed-age couples (SPCA 2002 s.4(1A), SI 2019/37 art. 4). The saving
   input never makes a unit eligible that has no member at the qualifying
   age, never changes a unit that is not a mixed-age couple, and never
   reduces eligibility.
"""

import datetime as dt

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

PROPERTY_SETTINGS = settings(
    max_examples=30,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)

# Pensions Act 1995 Sch. 4 para. 1, Table 1 (women born 6 April 1950 to
# 5 December 1953): (born from, born to, pensionable age date), copied from
# https://www.legislation.gov.uk/ukpga/1995/26/schedule/4/paragraph/1.
PENSIONS_ACT_1995_SCHEDULE_4_TABLE_1 = [
    ((1950, 4, 6), (1950, 5, 5), (2010, 5, 6)),
    ((1950, 5, 6), (1950, 6, 5), (2010, 7, 6)),
    ((1950, 6, 6), (1950, 7, 5), (2010, 9, 6)),
    ((1950, 7, 6), (1950, 8, 5), (2010, 11, 6)),
    ((1950, 8, 6), (1950, 9, 5), (2011, 1, 6)),
    ((1950, 9, 6), (1950, 10, 5), (2011, 3, 6)),
    ((1950, 10, 6), (1950, 11, 5), (2011, 5, 6)),
    ((1950, 11, 6), (1950, 12, 5), (2011, 7, 6)),
    ((1950, 12, 6), (1951, 1, 5), (2011, 9, 6)),
    ((1951, 1, 6), (1951, 2, 5), (2011, 11, 6)),
    ((1951, 2, 6), (1951, 3, 5), (2012, 1, 6)),
    ((1951, 3, 6), (1951, 4, 5), (2012, 3, 6)),
    ((1951, 4, 6), (1951, 5, 5), (2012, 5, 6)),
    ((1951, 5, 6), (1951, 6, 5), (2012, 7, 6)),
    ((1951, 6, 6), (1951, 7, 5), (2012, 9, 6)),
    ((1951, 7, 6), (1951, 8, 5), (2012, 11, 6)),
    ((1951, 8, 6), (1951, 9, 5), (2013, 1, 6)),
    ((1951, 9, 6), (1951, 10, 5), (2013, 3, 6)),
    ((1951, 10, 6), (1951, 11, 5), (2013, 5, 6)),
    ((1951, 11, 6), (1951, 12, 5), (2013, 7, 6)),
    ((1951, 12, 6), (1952, 1, 5), (2013, 9, 6)),
    ((1952, 1, 6), (1952, 2, 5), (2013, 11, 6)),
    ((1952, 2, 6), (1952, 3, 5), (2014, 1, 6)),
    ((1952, 3, 6), (1952, 4, 5), (2014, 3, 6)),
    ((1952, 4, 6), (1952, 5, 5), (2014, 5, 6)),
    ((1952, 5, 6), (1952, 6, 5), (2014, 7, 6)),
    ((1952, 6, 6), (1952, 7, 5), (2014, 9, 6)),
    ((1952, 7, 6), (1952, 8, 5), (2014, 11, 6)),
    ((1952, 8, 6), (1952, 9, 5), (2015, 1, 6)),
    ((1952, 9, 6), (1952, 10, 5), (2015, 3, 6)),
    ((1952, 10, 6), (1952, 11, 5), (2015, 5, 6)),
    ((1952, 11, 6), (1952, 12, 5), (2015, 7, 6)),
    ((1952, 12, 6), (1953, 1, 5), (2015, 9, 6)),
    ((1953, 1, 6), (1953, 2, 5), (2015, 11, 6)),
    ((1953, 2, 6), (1953, 3, 5), (2016, 1, 6)),
    ((1953, 3, 6), (1953, 4, 5), (2016, 3, 6)),
    ((1953, 4, 6), (1953, 5, 5), (2016, 7, 6)),
    ((1953, 5, 6), (1953, 6, 5), (2016, 11, 6)),
    ((1953, 6, 6), (1953, 7, 5), (2017, 3, 6)),
    ((1953, 7, 6), (1953, 8, 5), (2017, 7, 6)),
    ((1953, 8, 6), (1953, 9, 5), (2017, 11, 6)),
    ((1953, 9, 6), (1953, 10, 5), (2018, 3, 6)),
    ((1953, 10, 6), (1953, 11, 5), (2018, 7, 6)),
    ((1953, 11, 6), (1953, 12, 5), (2018, 11, 6)),
]

SAVINGS_CREDIT_CUTOFF = dt.date(2016, 4, 6)


def _anniversary(born, years):
    try:
        return born.replace(year=born.year + years)
    except ValueError:  # 29 February
        return dt.date(born.year + years, 3, 1)


def _pensionable_age_date(born, male):
    """Date of attaining pensionable age, or None if on or after 6 April 2016."""
    if male:
        # Sch. 4 para. 1(1): 65 for a man born before 6 December 1953.
        if born < dt.date(1953, 12, 6):
            return _anniversary(born, 65)
        return None
    # Sch. 4 para. 1(2): 60 for a woman born before 6 April 1950.
    if born < dt.date(1950, 4, 6):
        return _anniversary(born, 60)
    for born_from, born_to, pension_date in PENSIONS_ACT_1995_SCHEDULE_4_TABLE_1:
        if dt.date(*born_from) <= born <= dt.date(*born_to):
            return dt.date(*pension_date)
    # Every later cohort attains pensionable age after 6 December 2018.
    return None


def _reference_savings_credit_age(year, age, male):
    if year < 2016:
        return age >= 65
    first = dt.date(year - age, 4, 6)
    last = dt.date(year - age + 1, 4, 5)
    outcomes = set()
    day = first
    while day <= last:
        pension_date = _pensionable_age_date(day, male)
        before_cutoff = (
            pension_date is not None and pension_date < SAVINGS_CREDIT_CUTOFF
        )
        # "has attained the age of 65 (before, on or after that date)": by the
        # end of the year from 6 April Y.
        attained_65 = _anniversary(day, 65) <= dt.date(year + 1, 4, 5)
        outcomes.add(before_cutoff and attained_65)
        day += dt.timedelta(days=1)
    assert len(outcomes) == 1, (year, age, male)
    return outcomes.pop()


def test_savings_credit_age_condition_matches_pensions_act_tables():
    ages = list(range(16, 101))
    for year in range(2012, 2041):
        people = {}
        expected = []
        for male in (True, False):
            for age in ages:
                name = f"{'m' if male else 'f'}{age}"
                people[name] = {
                    "age": {year: age},
                    "gender": {year: "MALE" if male else "FEMALE"},
                }
                expected.append(_reference_savings_credit_age(year, age, male))
        sim = Simulation(
            situation={
                "people": people,
                "benunits": {n: {"members": [n]} for n in people},
                "households": {n: {"members": [n]} for n in people},
            }
        )
        got = sim.calculate("meets_savings_credit_age_requirement", year)
        mismatches = [
            (name, bool(g), e)
            for name, g, e in zip(people, got, expected)
            if bool(g) != e
        ]
        assert not mismatches, (year, mismatches)


# Severe disability addition.

MEMBER = st.fixed_dictionaries(
    {
        # "dla_lowest" is a disability benefit that does not qualify.
        "benefit": st.sampled_from([None, "aa", "pip", "dla_lowest"]),
        "hospital_aa_or_dla": st.booleans(),
        "hospital_daily_living": st.booleans(),
        "blind": st.booleans(),
        "receives_carers_allowance": st.booleans(),
    }
)
BENEFIT_UNIT = st.fixed_dictionaries(
    {
        "claimant": MEMBER,
        "partner": st.one_of(st.none(), MEMBER),
        # A dependant: a 17-year-old carer, an 18-year-old qualifying young
        # person, or a 19-year-old past the reg 4A terminal date.
        "dependant": st.sampled_from([None, "carer_17", "qyp_18", "past_19"]),
    }
)
OTHER_ADULT = st.fixed_dictionaries(
    {
        "age": st.sampled_from([17, 18, 45]),
        "in_receipt": st.booleans(),
        "blind": st.booleans(),
        "ignored": st.booleans(),
    }
)
HOUSEHOLD = st.fixed_dictionaries(
    {
        "units": st.lists(BENEFIT_UNIT, min_size=1, max_size=2),
        "other_adult": st.one_of(st.none(), OTHER_ADULT),
    }
)


def _in_receipt(member):
    return member["benefit"] in ("aa", "pip")


def _member_person(member, age):
    person = {"age": {2026: age}}
    if member["benefit"] == "aa":
        person["attendance_allowance"] = {2026: 5_000}
    elif member["benefit"] == "pip":
        person["pip_dl"] = {2026: 5_000}
    elif member["benefit"] == "dla_lowest":
        person["dla_sc_category"] = {2026: "LOWER"}
    if member["hospital_aa_or_dla"]:
        person["would_receive_aa_or_dla_care_but_for_hospital_stay"] = {2026: True}
    if member["hospital_daily_living"]:
        person[
            "would_receive_daily_living_disability_benefit_but_for_hospital_stay"
        ] = {2026: True}
    if member["blind"]:
        person["is_blind"] = {2026: True}
    if member["receives_carers_allowance"]:
        person["carers_allowance_reported"] = {2026: 1}
    return person


DEPENDANTS = {
    "carer_17": {"age": {2026: 17}, "carers_allowance_reported": {2026: 1}},
    "qyp_18": {"age": {2026: 18}, "current_education": {2026: "UPPER_SECONDARY"}},
    "past_19": {
        "age": {2026: 19},
        "current_education": {2026: "UPPER_SECONDARY"},
        "age_started_or_accepted_current_education_or_training": {2026: 18},
    },
}


def _reference_severe_disability_multiple(household, u):
    """Rate multiple for unit u from the Sch. I paras 1-2 and reg. 6(5) text."""
    unit = household["units"][u]
    claimants = [unit["claimant"]] + ([unit["partner"]] if unit["partner"] else [])
    # Adults residing with this unit's claimant or partner who para 2 does
    # not ignore: other units' claimants and partners, their 19-year-olds
    # past the terminal date, this unit's own such 19-year-old, and the other
    # adult. Qualifying young people (18) and under-18s are ignored.
    residents = []
    for v, other in enumerate(household["units"]):
        if v != u:
            residents += [other["claimant"]] + (
                [other["partner"]] if other["partner"] else []
            )
    barred = any(not (_in_receipt(r) or r["blind"]) for r in residents)
    barred |= any(unit_["dependant"] == "past_19" for unit_ in household["units"])
    other = household["other_adult"]
    if other is not None and other["age"] >= 18:
        barred |= not (other["in_receipt"] or other["blind"] or other["ignored"])
    if barred:
        return 0
    carers = [c["receives_carers_allowance"] for c in claimants]
    carers.append(unit["dependant"] == "carer_17")
    # A carer benefit received by another member is for caring for this
    # claimant or partner; each carer cares for one person (SSCBA s.70(7)).
    cared_for = [sum(carers) - carers[i] > 0 for i in range(len(claimants))]
    if len(claimants) == 1:
        return int(_in_receipt(claimants[0]) and not cared_for[0])
    number_cared_for = min(sum(cared_for), sum(carers))
    treated = [
        _in_receipt(c) or c["hospital_aa_or_dla"] or c["hospital_daily_living"]
        for c in claimants
    ]
    if all(treated) and number_cared_for <= 1:
        without_para_1_2_b = all(
            _in_receipt(c) or c["hospital_daily_living"] for c in claimants
        )
        return 2 if without_para_1_2_b and number_cared_for == 0 else 1
    head_c = any(
        _in_receipt(claimants[i]) and not cared_for[i] and claimants[1 - i]["blind"]
        for i in range(2)
    )
    return int(head_c)


@PROPERTY_SETTINGS
@given(households=st.lists(HOUSEHOLD, min_size=1, max_size=8))
def test_severe_disability_addition_matches_regulation_text(households):
    people, benunits, household_members = {}, {}, {}
    for h, household in enumerate(households):
        members = []
        for u, unit in enumerate(household["units"]):
            key = f"{h}_{u}"
            unit_members = [f"c{key}"]
            people[f"c{key}"] = _member_person(unit["claimant"], 80)
            if unit["partner"]:
                unit_members.append(f"p{key}")
                people[f"p{key}"] = _member_person(unit["partner"], 78)
            if unit["dependant"]:
                unit_members.append(f"d{key}")
                people[f"d{key}"] = dict(DEPENDANTS[unit["dependant"]])
                people[f"c{key}"]["is_parent"] = {2026: True}
            benunits[f"b{key}"] = {"members": unit_members}
            members += unit_members
        other = household["other_adult"]
        if other:
            people[f"o{h}"] = {"age": {2026: other["age"]}}
            if other["in_receipt"]:
                people[f"o{h}"]["pip_dl"] = {2026: 5_000}
            if other["blind"]:
                people[f"o{h}"]["is_blind"] = {2026: True}
            if other["ignored"]:
                people[f"o{h}"][
                    "is_ignored_resident_for_pension_credit_severe_disability"
                ] = {2026: True}
            benunits[f"ob{h}"] = {"members": [f"o{h}"]}
            members.append(f"o{h}")
        household_members[f"h{h}"] = {"members": members}
    sim = Simulation(
        situation={
            "people": people,
            "benunits": benunits,
            "households": household_members,
        }
    )
    weekly = float(
        sim.tax_benefit_system.parameters(
            "2026"
        ).gov.dwp.pension_credit.guarantee_credit.severe_disability.addition
    )
    # Benefit units come back in the order the situation lists them.
    amounts = sim.calculate("severe_disability_minimum_guarantee_addition", 2026)
    order = list(benunits)
    for h, household in enumerate(households):
        for u, unit in enumerate(household["units"]):
            amount = float(amounts[order.index(f"b{h}_{u}")])
            multiple = amount / (weekly * 52)
            assert abs(multiple - round(multiple)) < 1e-4, (household, u, amount)
            allowed = (0, 1, 2) if unit["partner"] else (0, 1)
            assert round(multiple) in allowed, (household, u, amount)
            assert round(multiple) == _reference_severe_disability_multiple(
                household, u
            ), (household, u, amount)


# Qualifying young person.

YOUNG_PERSON = st.fixed_dictionaries(
    {
        "age": st.integers(14, 21),
        "education": st.sampled_from(
            ["NOT_IN_EDUCATION", "UPPER_SECONDARY", "TERTIARY"]
        ),
        "approved_training": st.booleans(),
        "entry_age": st.integers(15, 20),
        "before_1_september_after_16th_birthday": st.booleans(),
        "before_1_september_after_19th_birthday": st.booleans(),
        "own_benefits": st.booleans(),
    }
)


def _reference_qualifying_young_person(y):
    """SPC Regs 2002 reg. 4A."""
    if not 16 <= y["age"] < 20 or y["own_benefits"]:  # 4A(1), 4A(5)
        return False
    # 4A(1)(a); the input asserts the date is still ahead.
    if y["before_1_september_after_16th_birthday"]:
        return True
    in_education = y["education"] == "UPPER_SECONDARY" or y["approved_training"]
    started_before_19 = y["age"] < 19 or y["entry_age"] < 19  # 4A(2)
    before_terminal_date = (
        y["age"] < 19 or y["before_1_september_after_19th_birthday"]
    )  # 4A(1)(b)
    return in_education and started_before_19 and before_terminal_date


@PROPERTY_SETTINGS
@given(young_people=st.lists(YOUNG_PERSON, min_size=1, max_size=20))
def test_qualifying_young_person_matches_regulation_4a(young_people):
    people = {}
    for n, y in enumerate(young_people):
        people[f"y{n}"] = {
            "age": {2026: y["age"]},
            "current_education": {2026: y["education"]},
            "is_in_approved_training": {2026: y["approved_training"]},
            "age_started_or_accepted_current_education_or_training": {
                2026: y["entry_age"]
            },
            "is_before_first_september_after_16th_birthday": {
                2026: y["before_1_september_after_16th_birthday"]
            },
            "is_before_first_september_after_19th_birthday": {
                2026: y["before_1_september_after_19th_birthday"]
            },
            "receives_benefits_in_own_right": {2026: y["own_benefits"]},
        }
    sim = Simulation(
        situation={
            "people": people,
            "benunits": {n: {"members": [n]} for n in people},
            "households": {n: {"members": [n]} for n in people},
        }
    )
    got = sim.calculate("is_qualifying_young_person_for_pension_credit", 2026)
    for y, g in zip(young_people, got):
        assert bool(g) == _reference_qualifying_young_person(y), y


# Mixed-age couples.

COUPLE = st.fixed_dictionaries(
    {
        "claimant_age": st.integers(50, 90),
        "partner_age": st.one_of(st.none(), st.integers(50, 90)),
    }
)


@PROPERTY_SETTINGS
@given(
    couples=st.lists(COUPLE, min_size=1, max_size=15),
    year=st.sampled_from([2018, 2019, 2020, 2026, 2030]),
)
def test_mixed_age_couple_saving_properties(couples, year):
    # Each couple appears twice in one simulation: without and with the saving.
    people, benunits, households = {}, {}, {}
    for protected in (False, True):
        for n, c in enumerate(couples):
            key = f"{int(protected)}_{n}"
            members = [f"c{key}"]
            people[f"c{key}"] = {"age": {year: c["claimant_age"]}}
            if c["partner_age"] is not None:
                members.append(f"p{key}")
                people[f"p{key}"] = {"age": {year: c["partner_age"]}}
            benunits[f"b{key}"] = {
                "members": members,
                "is_protected_mixed_age_couple_for_pension_credit": {year: protected},
            }
            households[f"h{key}"] = {"members": list(members)}
    sim = Simulation(
        situation={"people": people, "benunits": benunits, "households": households}
    )
    sp_age = np.asarray(sim.calculate("is_SP_age", year, map_to="benunit"))
    claimants = np.asarray(
        sim.calculate("is_claimant_or_partner", year, map_to="benunit")
    )
    eligible = np.asarray(sim.calculate("is_pension_credit_eligible", year))
    half = len(couples)
    unprotected, protected = eligible[:half], eligible[half:]
    sp_age, claimants = sp_age[:half], claimants[:half]
    mixed_age = (sp_age > 0) & (sp_age < claimants)
    # The saving never reduces eligibility.
    assert np.all(protected >= unprotected)
    # It never makes a unit with no member at the qualifying age eligible.
    assert not np.any(protected & (sp_age == 0))
    # It changes nothing for a unit that is not a mixed-age couple.
    assert np.all(protected[~mixed_age] == unprotected[~mixed_age])
    # With zero income, a mixed-age couple is eligible exactly when the
    # s.4(1A) exclusion is not yet in force or the saving applies.
    exclusion_in_force = year >= 2020  # 15 May 2019, sampled at 30 April.
    assert np.all(unprotected[mixed_age] == (not exclusion_in_force))
    assert np.all(protected[mixed_age])
