"""Care to Learn, extended childcare, maintenance loan and Tax-Free Childcare.

Each property compares the model with an independent scalar reference written
from the source below, over randomly drawn families batched into one
Simulation per example.

Invariants:

1. Care to Learn (ESFA conditions of grant 2026-27, sections 1.2, 2.2, 2.3,
   4.1). For each benefit unit the amounts paid sum to the sum over the
   Child Benefit children of min(childcare costs, weekly maximum x 52) when
   some parent is eligible, and to 0 otherwise. Eligible means under 20, in
   non-higher education, not an apprentice and living in England. At most one
   person is paid, the eldest eligible parent. Each child adds at most the
   per-child cap.
2. Extended childcare (SI 2022/1134 regs 11A, 13-15 and 18). A family is
   eligible if and only if it has a young child of the minimum age for the
   year (3, 2 in 2024, nine months from 2025), under 5 and not looked after.
   Each claimant or partner must also meet reg 14(3)/15(3), meaning earnings
   of at least 16 x minimum wage x 13 a quarter and adjusted net income of at
   most £100,000, or meet reg 14(4)/15(4): a specified benefit or limited
   capability for work, with a partner who meets reg 14(3)/15(3). PIP never
   matters.
3. Tax-Free Childcare work condition (SI 2015/448 reg 13). Each applicant or
   partner is in work, or receives a reg 13(1)(b) benefit and has a partner in
   work who receives none (reg 13(3)). DLA, PIP and income-related ESA never
   matter. Reg 13(2)(b) deems the minimum income for anyone regarded as in
   paid work.
4. Maintenance loan household income (SI 2011/1986 Sch 4 para 2(1)(a)). A
   student's assessed income is their own benefit unit's income plus the
   sponsor's only if they are under 25 and the model detects a sponsor. At 25
   or over it is exactly their own, so it never falls when the sponsor's
   income falls, and never exceeds the dependent-student figure.

Scope: these test the encoded conditions, not full entitlement. Travel costs
under Care to Learn, the reg 16/17 leave exemptions and National Insurance
number conditions of the extended entitlement, and Sch 4 para 2(1)(b)-(k)
beyond the couple and parent proxies are not modelled. Sources were fetched on
2026-09-28:
https://www.gov.uk/government/publications/care-to-learn-conditions-of-grant-funding/care-to-learn-academic-year-2026-to-2027-conditions-of-grant-funding
https://www.legislation.gov.uk/uksi/2022/1134/regulation/13
https://www.legislation.gov.uk/uksi/2022/1134/regulation/14
https://www.legislation.gov.uk/uksi/2022/1134/regulation/15
https://www.legislation.gov.uk/uksi/2022/1134/regulation/11A
https://www.legislation.gov.uk/uksi/2022/1134/regulation/18
https://www.legislation.gov.uk/uksi/2023/1330/regulation/2/made
https://www.legislation.gov.uk/uksi/2015/448/regulation/13
https://www.legislation.gov.uk/uksi/2011/1986/schedule/4
"""

from unittest.mock import patch

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.tax_benefit_system import system

_PROPERTY_SYSTEM = system.clone()
PROPERTY_SETTINGS = settings(
    max_examples=25,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
EDUCATIONS = (
    "NOT_IN_EDUCATION",
    "LOWER_SECONDARY",
    "UPPER_SECONDARY",
    "POST_SECONDARY",
    "TERTIARY",
)
MINIMUM_WAGE = 10
# Reg 18: 16 hours x minimum wage x 13 weeks.
QUARTERLY_MINIMUM = MINIMUM_WAGE * 16 * 13
INCOME_LIMIT = 100_000


def simulate(families, year):
    """One Simulation for many families, each its own benefit unit and household.

    A family is (people, benunit_inputs, household_inputs), where people is a
    list of per-person input dicts.
    """
    situation = {"people": {}, "benunits": {}, "households": {}}
    names = []
    for i, (people, benunit_inputs, household_inputs) in enumerate(families):
        members = []
        for j, inputs in enumerate(people):
            name = f"p{i}_{j}"
            situation["people"][name] = {k: {year: v} for k, v in inputs.items()}
            members.append(name)
            names.append((i, j))
        situation["benunits"][f"b{i}"] = {
            "members": members,
            **{k: {year: v} for k, v in benunit_inputs.items()},
        }
        situation["households"][f"h{i}"] = {
            "members": members,
            **{k: {year: v} for k, v in household_inputs.items()},
        }
    with patch(
        "policyengine_uk.simulation.CountryTaxBenefitSystem",
        side_effect=_PROPERTY_SYSTEM.clone,
    ):
        sim = Simulation(situation=situation)
    return sim, names


def by_family(values, names, n_families):
    out = [[] for _ in range(n_families)]
    for value, (i, _) in zip(values, names):
        out[i].append(value)
    return out


def close(a, b):
    return abs(a - b) <= 0.02 + 1e-6 * abs(b)


# 1. Care to Learn ---------------------------------------------------------


young_parent = st.fixed_dictionaries(
    {
        "age": st.integers(14, 22),
        "current_education": st.sampled_from(EDUCATIONS),
        "is_apprentice": st.booleans(),
    }
)
child_costs = st.lists(
    st.tuples(st.integers(0, 5), st.sampled_from([0, 1_000, 9_360, 10_140, 25_000])),
    min_size=0,
    max_size=3,
)
care_to_learn_family = st.tuples(
    st.lists(young_parent, min_size=1, max_size=2),
    child_costs,
    st.sampled_from(["LONDON", "NORTH_EAST"]),
)


def care_to_learn_eligible_reference(parent, n_children):
    return (
        n_children > 0
        and parent["age"] < 20
        and parent["current_education"] not in {"NOT_IN_EDUCATION", "TERTIARY"}
        and not parent["is_apprentice"]
    )


@PROPERTY_SETTINGS
@given(st.lists(care_to_learn_family, min_size=1, max_size=6))
def test_care_to_learn_pays_each_child_once_up_to_the_per_child_cap(families):
    built = []
    for parents, children, region in families:
        people = [{**p, "is_parent": True} for p in parents] + [
            {"age": age, "childcare_expenses": cost} for age, cost in children
        ]
        built.append((people, {}, {"country": "ENGLAND", "region": region}))
    sim, names = simulate(built, 2025)
    paid = by_family(sim.calculate("care_to_learn", 2025), names, len(families))

    for (parents, children, region), amounts in zip(families, paid):
        cap = (195 if region == "LONDON" else 180) * 52
        eligible = [care_to_learn_eligible_reference(p, len(children)) for p in parents]
        expected = sum(min(cost, cap) for _, cost in children) if any(eligible) else 0
        assert close(sum(amounts), expected), (parents, children, region, amounts)
        assert sum(amount > 0 for amount in amounts) <= 1
        assert sum(amounts) <= len(children) * cap + 0.02
        if expected > 0:
            # The one payment goes to an eligible parent of the greatest age.
            eldest_age = max(p["age"] for k, p in enumerate(parents) if eligible[k])
            paid_to = [k for k in range(len(parents)) if amounts[k] > 0]
            assert len(paid_to) == 1
            assert eligible[paid_to[0]]
            assert parents[paid_to[0]]["age"] == eldest_age
        # Children are never paid.
        assert all(a == 0 for a in amounts[len(parents) :])


# 2. Extended childcare ----------------------------------------------------


STATUS_INPUTS = {
    "carers_allowance": 4_000,
    "esa_contrib": 4_000,
    "incapacity_benefit": 4_000,
    "uc_limited_capability_for_WRA": True,
    "receives_limited_capability_for_work_credits": True,
}
extended_adult = st.fixed_dictionaries(
    {
        "age": st.integers(20, 60),
        "earnings": st.sampled_from([0, 8_316, 8_320, 20_000, 100_000, 100_001]),
        "status": st.sampled_from([None, *STATUS_INPUTS]),
        "pip": st.sampled_from([0, 5_000]),
    }
)
extended_child = st.tuples(st.sampled_from([0.5, 0.75, 1, 2, 3, 4, 6]), st.booleans())
extended_family = st.tuples(
    st.lists(extended_adult, min_size=1, max_size=2),
    st.lists(extended_child, min_size=0, max_size=2),
)
YOUNG_CHILD_MINIMUM_AGE = {2023: 3, 2024: 2, 2025: 0.75, 2026: 0.75}


def meets_work_and_income(adult):
    earnings = adult["earnings"]
    return (
        earnings > 0 and earnings / 4 >= QUARTERLY_MINIMUM and earnings <= INCOME_LIMIT
    )


@PROPERTY_SETTINGS
@given(
    st.sampled_from([2023, 2024, 2025, 2026]),
    st.lists(extended_family, min_size=1, max_size=6),
)
def test_extended_childcare_eligibility_matches_regs_13_to_15(year, families):
    built = []
    for adults, children in families:
        people = []
        for adult in adults:
            inputs = {
                "age": adult["age"],
                "is_parent": bool(children),
                "employment_income": adult["earnings"],
                "adjusted_net_income": adult["earnings"],
                "minimum_wage": MINIMUM_WAGE,
                "pip": adult["pip"],
            }
            if adult["status"]:
                inputs[adult["status"]] = STATUS_INPUTS[adult["status"]]
            people.append(inputs)
        for age, looked_after in children:
            people.append(
                {"age": age, "is_looked_after_by_local_authority": looked_after}
            )
        built.append((people, {}, {"country": "ENGLAND"}))
    sim, _ = simulate(built, year)
    eligible = sim.calculate("extended_childcare_entitlement_eligible", year)

    minimum_age = YOUNG_CHILD_MINIMUM_AGE[year]
    for (adults, children), result in zip(families, eligible):
        has_young_child = any(
            minimum_age <= age < 5 and not looked_after
            for age, looked_after in children
        )
        meets = [meets_work_and_income(a) for a in adults]
        ok = [
            meets[k]
            or (
                adults[k]["status"] is not None
                and any(meets[m] for m in range(len(adults)) if m != k)
            )
            for k in range(len(adults))
        ]
        assert bool(result) == (has_young_child and all(ok)), (
            year,
            adults,
            children,
        )


# 3. Tax-Free Childcare ----------------------------------------------------


REG_13_BENEFITS = {
    "carers_allowance": 4_000,
    "incapacity_benefit": 4_000,
    "sda": 4_000,
    "esa_contrib": 4_000,
    "carer_support_payment": 4_000,
    "receives_limited_capability_for_work_credits": True,
}
NOT_REG_13 = {"dla": 4_000, "pip": 4_000}
tfc_adult = st.fixed_dictionaries(
    {
        "in_work": st.booleans(),
        "benefit": st.sampled_from([None, *REG_13_BENEFITS]),
        "other": st.sampled_from([None, *NOT_REG_13]),
    }
)
tfc_family = st.tuples(st.lists(tfc_adult, min_size=1, max_size=2), st.booleans())


@PROPERTY_SETTINGS
@given(st.lists(tfc_family, min_size=1, max_size=8))
def test_tax_free_childcare_work_condition_matches_reg_13(families):
    built = []
    for adults, income_related_esa in families:
        people = []
        for adult in adults:
            inputs = {
                "age": 35,
                "in_work": adult["in_work"],
                "adjusted_net_income": 20_000,
                "minimum_wage": MINIMUM_WAGE,
            }
            if adult["benefit"]:
                inputs[adult["benefit"]] = REG_13_BENEFITS[adult["benefit"]]
            if adult["other"]:
                inputs[adult["other"]] = NOT_REG_13[adult["other"]]
            people.append(inputs)
        people.append({"age": 3})
        benunit = {"esa_income": 4_000} if income_related_esa else {}
        built.append((people, benunit, {"country": "ENGLAND"}))
    sim, names = simulate(built, 2025)
    work = by_family(
        sim.calculate("tax_free_childcare_work_condition", 2025),
        names,
        len(families),
    )
    regarded = by_family(
        sim.calculate("tax_free_childcare_regarded_as_in_paid_work", 2025),
        names,
        len(families),
    )
    meets_income = by_family(
        sim.calculate("tax_free_childcare_meets_income_requirements", 2025),
        names,
        len(families),
    )

    for (adults, _), work_values, regarded_values, income_values in zip(
        families, work, regarded, meets_income
    ):
        has_benefit = [a["benefit"] is not None for a in adults]
        reference_regarded = [
            has_benefit[k]
            and any(
                adults[m]["in_work"] and not has_benefit[m]
                for m in range(len(adults))
                if m != k
            )
            for k in range(len(adults))
        ]
        family_meets = all(
            adults[k]["in_work"] or reference_regarded[k] for k in range(len(adults))
        )
        n = len(adults)
        assert [bool(v) for v in regarded_values[:n]] == reference_regarded
        assert [bool(v) for v in work_values[:n]] == [family_meets] * n
        assert not work_values[n]  # the child
        # Reg 13(2)(b): regarded as having the minimum income.
        for k in range(n):
            if reference_regarded[k]:
                assert income_values[k]


# 4. Maintenance loan household income ---------------------------------------


student_household = st.fixed_dictionaries(
    {
        "parent_age": st.integers(35, 70),
        "parent_income": st.sampled_from([0, 15_000, 40_000, 90_000]),
        "student_age": st.integers(18, 35),
        "student_income": st.sampled_from([0, 5_000, 12_000]),
    }
)


@PROPERTY_SETTINGS
@given(st.lists(student_household, min_size=1, max_size=6))
def test_maintenance_loan_household_income_applies_the_age_25_test(households):
    situation = {"people": {}, "benunits": {}, "households": {}}
    year = 2025
    for i, h in enumerate(households):
        parent, student = f"parent{i}", f"student{i}"
        situation["people"][parent] = {
            "age": {year: h["parent_age"]},
            "current_education": {year: "NOT_IN_EDUCATION"},
            "adjusted_net_income": {year: h["parent_income"]},
            "is_household_head": {year: True},
        }
        situation["people"][student] = {
            "age": {year: h["student_age"]},
            "current_education": {year: "TERTIARY"},
            "adjusted_net_income": {year: h["student_income"]},
            "is_household_head": {year: False},
        }
        situation["benunits"][f"pb{i}"] = {"members": [parent]}
        situation["benunits"][f"sb{i}"] = {"members": [student]}
        situation["households"][f"h{i}"] = {
            "members": [parent, student],
            "country": {year: "ENGLAND"},
        }
    with patch(
        "policyengine_uk.simulation.CountryTaxBenefitSystem",
        side_effect=_PROPERTY_SYSTEM.clone,
    ):
        sim = Simulation(situation=situation)
    income = sim.calculate("maintenance_loan_household_income", year).reshape(-1, 2)

    for h, (parent_value, student_value) in zip(households, income):
        age, parent_age = h["student_age"], h["parent_age"]
        has_sponsor = parent_age >= 29 and age + 10 <= parent_age <= age + 35
        dependent = age < 25 and has_sponsor
        expected = h["student_income"] + dependent * h["parent_income"]
        assert close(student_value, expected), h
        assert close(parent_value, h["parent_income"]), h
        # Independence never adds the parents' income.
        if age >= 25:
            assert close(student_value, h["student_income"]), h
        assert student_value >= h["student_income"] - 0.02
