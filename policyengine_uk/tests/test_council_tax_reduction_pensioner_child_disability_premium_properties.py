"""Property-based tests for a pensioner's Council Tax Reduction child
disability premiums.

Councils add the disabled child premium and the enhanced disability premium
to a pensioner's applicable amount for each qualifying child or young person
in the family (SI 2012/2885 Sch 1 para 6(1)(d) and Sch 2 paras 7, 8 and Part
4; WSI 2013/3029 Sch 1 para 1(1)(d) and Sch 2 paras 7, 8 and 12; SSI 2012/319
reg 20(d) and Sch 1 paras 8, 9 and 13). A child or young person meets the
disabled child condition with DLA or PIP (either component) or blindness, and
the enhanced condition with the highest DLA care rate or the enhanced PIP
daily living rate. The armed forces independence payment (AFIP) meets a
condition where the nation's scheme names it for that person in that year
(AFIP_ROUTES).

The test generates families in England, Wales and Scotland with children and
young persons on the listed awards, and checks these invariants:

1. Working-age families, and a pensioner household head who applies alone,
   get no child disability premium.
2. A pensioner family's premiums equal the sum, over its children and young
   persons, of 52 times each premium whose condition the child meets, at the
   weekly amounts in AMOUNTS.
3. On the model's inputs, every child or young person who meets the enhanced
   condition also meets the disabled child condition, except through AFIP:
   a child under 16 on AFIP alone meets only the enhanced condition in
   England from 2023 and in Wales before 2024.
4. The applicable amount never falls when a child or young person gains a
   qualifying benefit.
5. For pension-age families with no AFIP, in every year from 2015 to 2026,
   the premiums equal housing_benefit_child_disability_premiums wherever
   is_child_or_young_person_for_council_tax_reduction and
   is_child_or_young_person_for_legacy_benefits agree.
"""

import numpy as np
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st
from policyengine_core.periods import period as make_period

from policyengine_uk import Simulation
from policyengine_uk.variables.gov.dwp.housing_benefit._child_disability_premiums import (
    child_disability_premium_benefit_conditions,
)

SETTINGS = settings(
    max_examples=6,
    deadline=None,
    derandomize=True,
    suppress_health_check=[
        HealthCheck.too_slow,
        HealthCheck.data_too_large,
        HealthCheck.filter_too_much,
    ],
)
WEEKS_IN_YEAR = 52
AUTHORITIES = {"ENGLAND": "MAIDSTONE", "WALES": "CARDIFF", "SCOTLAND": "GLASGOW_CITY"}
YEARS = list(range(2015, 2027))
# Weekly (enhanced disability premium, disabled child premium) for each child
# or young person, the same in all three nations from 2014-15 (each schedule's
# table of premium amounts in force on 30 April).
AMOUNTS = {
    2015: (24.43, 60.06),
    2016: (24.43, 60.06),
    2017: (24.78, 60.90),
    2018: (25.48, 62.86),
    2019: (26.04, 64.19),
    2020: (26.60, 65.52),
    2021: (26.67, 65.94),
    2022: (27.44, 68.04),
    2023: (30.17, 74.69),
    2024: (32.20, 80.01),
    2025: (32.75, 81.37),
    2026: (33.99, 84.46),
}


def afip_routes(country, year, young_person):
    """Whether AFIP meets the (enhanced, disabled child) condition: England
    paras 7(1)(c) and 8(e) from 2023-24 (SI 2023/16); Wales para 7(1)(c), and
    para 8(d) from 2024-25 (WSI 2024/56); Scotland paras 8(1)(aa) and 9(ba),
    for a young person only."""
    if country == "ENGLAND":
        return year >= 2023, year >= 2023 and young_person
    if country == "WALES":
        return True, year >= 2024
    return young_person, young_person


# Award inputs, and whether each meets the (disabled child, enhanced)
# condition on its own.
AWARDS = {
    "dla_care_lowest": ({"dla_sc_category": "LOWER"}, True, False),
    "dla_care_middle": ({"dla_sc_category": "MIDDLE"}, True, False),
    "dla_care_highest": ({"dla_sc_category": "HIGHER"}, True, True),
    "dla_mobility_lower": ({"dla_m_category": "LOWER"}, True, False),
    "pip_daily_living_standard": ({"pip_dl_category": "STANDARD"}, True, False),
    "pip_daily_living_enhanced": ({"pip_dl_category": "ENHANCED"}, True, True),
    "pip_mobility_standard": ({"pip_m_category": "STANDARD"}, True, False),
    "blind": ({"is_blind": True}, True, False),
    "afip": ({"armed_forces_independence_payment": 2_000}, False, False),
}
# A child under 16, a Child Benefit qualifying young person (17 and at
# school) and a 17-year-old out of education, who is neither.
KINDS = ("child", "young_person", "not_counted")

child_strategy = st.fixed_dictionaries(
    {
        "kind": st.sampled_from(KINDS),
        "age": st.integers(0, 15),
        # Two awards never set the same input.
        "awards": st.lists(
            st.sampled_from(list(AWARDS)),
            max_size=2,
            unique_by=lambda award: tuple(AWARDS[award][0]),
        ),
    }
)
pensioner_family = st.fixed_dictionaries(
    {
        "country": st.sampled_from(list(AUTHORITIES)),
        "age": st.integers(67, 90),
        "partner_age": st.one_of(st.none(), st.integers(60, 90)),
        "claims_pc": st.booleans(),
        "children": st.lists(child_strategy, min_size=1, max_size=3),
    }
)
working_age_family = st.fixed_dictionaries(
    {
        "country": st.sampled_from(list(AUTHORITIES)),
        "age": st.integers(25, 55),
        "partner_age": st.one_of(st.none(), st.integers(25, 55)),
        "claims_pc": st.just(False),
        "children": st.lists(child_strategy, min_size=1, max_size=3),
    }
)


def child_inputs(child, year):
    if child["kind"] == "child":
        inputs = {"age": child["age"]}
    else:
        inputs = {"age": 17}
        if child["kind"] == "young_person":
            inputs["current_education"] = "UPPER_SECONDARY"
            inputs["age_started_or_accepted_current_education_or_training"] = 16
    for award in child["awards"]:
        inputs.update(AWARDS[award][0])
    return {name: {year: value} for name, value in inputs.items()}


def situation(families, year, head_alone=()):
    """One benefit unit and household for each family, and for each family
    in head_alone a pensioner household head who applies alone, with that
    family's adults as the claimant couple in her benefit unit."""
    data = {"people": {}, "benunits": {}, "households": {}}
    for index, spec in enumerate(families):
        alone = index in head_alone
        members = []
        if alone:
            name = f"head_{index}"
            data["people"][name] = {
                "age": {year: 80},
                "is_household_head": {year: True},
            }
            members.append(name)
        adults = [spec["age"]]
        if spec["partner_age"] is not None or alone:
            adults.append(spec["partner_age"] or spec["age"])
        for number, age in enumerate(adults):
            name = f"adult_{index}_{number}"
            person = {"age": {year: age}}
            if alone:
                person["is_parent"] = {year: True}
                person["is_household_head"] = {year: False}
            data["people"][name] = person
            members.append(name)
        for number, child in enumerate(spec["children"]):
            name = f"child_{index}_{number}"
            data["people"][name] = child_inputs(child, year)
            if alone:
                data["people"][name]["is_household_head"] = {year: False}
            members.append(name)
        data["benunits"][f"family_{index}"] = {
            "members": members,
            "would_claim_pc": {year: spec["claims_pc"]},
            "would_claim_uc": {year: False},
        }
        data["households"][f"home_{index}"] = {
            "members": members,
            "country": {year: spec["country"]},
            "local_authority": {year: AUTHORITIES[spec["country"]]},
            "tenure_type": {year: "OWNED_OUTRIGHT"},
            "council_tax": {year: 2_000},
            "savings": {year: 0},
        }
    return data


def child_premiums(child, country, year):
    """The test's own annual premiums for one child or young person."""
    if child["kind"] == "not_counted":
        return 0.0
    enhanced_amount, disabled_amount = AMOUNTS[year]
    disabled = any(AWARDS[award][1] for award in child["awards"])
    enhanced = any(AWARDS[award][2] for award in child["awards"])
    if "afip" in child["awards"]:
        afip_enhanced, afip_disabled = afip_routes(
            country, year, child["kind"] == "young_person"
        )
        disabled = disabled or afip_disabled
        enhanced = enhanced or afip_enhanced
    return WEEKS_IN_YEAR * (disabled_amount * disabled + enhanced_amount * enhanced)


def calculate(families, year, names, head_alone=()):
    simulation = Simulation(situation=situation(families, year, head_alone))
    return {name: np.asarray(simulation.calculate(name, year)) for name in names}


@SETTINGS
@given(
    st.lists(working_age_family, min_size=1, max_size=4),
    st.lists(pensioner_family, min_size=1, max_size=3),
    st.sampled_from(YEARS),
)
def test_nil_for_working_age_families_and_a_head_who_applies_alone(
    working_age, pensioners, year
):
    families = working_age + pensioners
    head_alone = set(range(len(working_age), len(families)))
    result = calculate(
        families,
        year,
        [
            "council_tax_reduction_pensioner",
            "council_tax_reduction_head_applies_alone",
            "council_tax_reduction_pensioner_child_disability_premiums",
        ],
        head_alone,
    )
    pensioner = result["council_tax_reduction_pensioner"]
    alone = result["council_tax_reduction_head_applies_alone"]
    # The generator builds what it means to build.
    assert not pensioner[: len(working_age)].any()
    assert alone[len(working_age) :].all()
    assert pensioner[len(working_age) :].all()
    np.testing.assert_array_equal(
        result["council_tax_reduction_pensioner_child_disability_premiums"], 0
    )


@SETTINGS
@given(
    st.lists(pensioner_family, min_size=1, max_size=6),
    st.sampled_from(YEARS),
)
def test_family_total_is_the_sum_of_each_childs_premiums(families, year):
    result = calculate(
        families,
        year,
        [
            "council_tax_reduction_pensioner",
            "council_tax_reduction_pensioner_child_disability_premiums",
        ],
    )
    assert result["council_tax_reduction_pensioner"].all()
    expected = [
        sum(child_premiums(child, spec["country"], year) for child in spec["children"])
        for spec in families
    ]
    np.testing.assert_allclose(
        result["council_tax_reduction_pensioner_child_disability_premiums"],
        expected,
        atol=0.01,
    )


@SETTINGS
@given(st.lists(child_strategy, min_size=1, max_size=8), st.sampled_from(YEARS))
def test_shared_enhanced_condition_implies_disabled_child_condition(children, year):
    families = [
        {
            "country": "ENGLAND",
            "age": 72,
            "partner_age": None,
            "claims_pc": False,
            "children": children,
        }
    ]
    simulation = Simulation(situation=situation(families, year))
    person = simulation.populations["person"]
    disabled, enhanced = child_disability_premium_benefit_conditions(
        person, make_period(year)
    )
    assert not (enhanced & ~disabled).any()


@SETTINGS
@given(
    st.sampled_from(list(AUTHORITIES)),
    st.sampled_from(YEARS),
    st.sampled_from(["child", "young_person"]),
    st.lists(
        st.sampled_from(list(AWARDS)),
        min_size=1,
        max_size=2,
        unique_by=lambda award: tuple(AWARDS[award][0]),
    ),
)
def test_enhanced_without_disabled_child_premium_only_through_afip(
    country, year, kind, awards
):
    child = {"kind": kind, "age": 10, "awards": awards}
    families = [
        {
            "country": country,
            "age": 72,
            "partner_age": None,
            "claims_pc": False,
            "children": [child],
        }
    ]
    total = calculate(
        families, year, ["council_tax_reduction_pensioner_child_disability_premiums"]
    )["council_tax_reduction_pensioner_child_disability_premiums"][0]
    enhanced_amount, disabled_amount = AMOUNTS[year]
    enhanced_only = abs(total - WEEKS_IN_YEAR * enhanced_amount) < 0.01
    # AFIP alone meets only the enhanced condition for a child under 16 in
    # England from 2023-24, and for any child or young person in Wales before
    # 2024-25.
    exception = awards == ["afip"] and (
        (country == "ENGLAND" and year >= 2023 and kind == "child")
        or (country == "WALES" and year < 2024)
    )
    assert enhanced_only == exception


@SETTINGS
@given(
    pensioner_family,
    st.sampled_from(YEARS),
    st.integers(0, 2),
    st.sampled_from(list(AWARDS)),
)
def test_applicable_amount_never_falls_when_a_child_gains_a_benefit(
    family, year, index, award
):
    index = index % len(family["children"])
    gained = dict(family)
    gained["children"] = [dict(child) for child in family["children"]]
    awards = gained["children"][index]["awards"]
    # The new award adds a benefit rather than replacing one the child has.
    assume(all(set(AWARDS[a][0]).isdisjoint(AWARDS[award][0]) for a in awards))
    gained["children"][index]["awards"] = awards + [award]
    result = calculate(
        [family, gained],
        year,
        [
            "council_tax_reduction_applicable_amount",
            "council_tax_reduction_pensioner_child_disability_premiums",
        ],
    )
    amount = result["council_tax_reduction_applicable_amount"]
    premiums = result["council_tax_reduction_pensioner_child_disability_premiums"]
    assert amount[1] >= amount[0] - 0.01
    assert premiums[1] >= premiums[0] - 0.01


@settings(
    max_examples=3,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
@given(
    st.lists(
        pensioner_family.map(
            lambda spec: {
                **spec,
                "children": [
                    {**child, "awards": [a for a in child["awards"] if a != "afip"]}
                    for child in spec["children"]
                ],
            }
        ),
        min_size=1,
        max_size=6,
    )
)
def test_matches_housing_benefit_child_premiums_without_afip(families):
    names = [
        "council_tax_reduction_pensioner",
        "council_tax_reduction_pensioner_child_disability_premiums",
        "housing_benefit_child_disability_premiums",
    ]
    for year in YEARS:
        simulation = Simulation(situation=situation(families, year))
        result = {name: np.asarray(simulation.calculate(name, year)) for name in names}
        council = np.asarray(
            simulation.calculate(
                "is_child_or_young_person_for_council_tax_reduction", year
            )
        )
        legacy = np.asarray(
            simulation.calculate("is_child_or_young_person_for_legacy_benefits", year)
        )
        agree = simulation.populations["benunit"].all(council == legacy)
        # For a pensioner's family the two definitions coincide.
        assert agree.all()
        compared = agree & result["council_tax_reduction_pensioner"]
        assert compared.all()
        np.testing.assert_allclose(
            result["council_tax_reduction_pensioner_child_disability_premiums"][
                compared
            ],
            result["housing_benefit_child_disability_premiums"][compared],
            atol=0.01,
        )
