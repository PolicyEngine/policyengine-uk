"""Housing Benefit family-premium contracts, not claim-history adjudication.

The saved family rules and 2016 closure instruments establish the routing
contracts below. Fixed 2015 and 2026 amounts are independently anchored in
YAML; 2027-2030 draws test declared parameters/projections, not future law.
See docs/engineering/housing-benefit-family-premium-tests.md for sources and
why the stronger category-minus-NONE identity is post-closure only.
"""

from itertools import product

import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.model_api import Scenario

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")
PROPERTY = settings(max_examples=12, deadline=None, derandomize=True)
YEARS = st.integers(min_value=2015, max_value=2030)
COUNTRIES = ("ENGLAND", "NORTHERN_IRELAND")
CATEGORIES = ("NONE", "ORDINARY_PROTECTED", "HISTORICAL_LONE_PARENT_PROTECTED")
PENNY = 0.01  # Annual float arrays; a penny, not uncertainty in the legal oracle.


def build(rows, year, scenario=None):
    """Independent units; regime/category flags isolate pre-assessed routing.

    Positive DLA/PIP inputs below are receipt-predicate sentinels, not statutory
    award amounts. A supplied adult premium is a separately assessed carer
    component with qualifying care/entitlement facts, not a test of its award.
    """
    people, benunits, households = {}, {}, {}
    for index, row in enumerate(rows):
        parent = f"u{index}parent"
        age = row.get("age", 40)
        people[parent] = {
            "age": {year: age},
            "is_male": {year: True},
            "is_parent": {year: True},
            "is_claimant_or_partner": {year: True},
        }
        members = [parent]
        if not row.get("lone", True):
            partner = f"u{index}partner"
            people[partner] = {
                "age": {year: age},
                "is_claimant_or_partner": {year: True},
            }
            members.append(partner)
        receipt = row.get("receipt", "none")
        for child_index in range(row.get("children", 1)):
            child = f"u{index}child{child_index}"
            people[child] = {
                "age": {year: 17 if receipt == "pip" else 1},
                "is_claimant_or_partner": {year: False},
                "is_child_or_young_person_for_legacy_benefits": {
                    year: row.get("included", True)
                },
                "dla_sc": {year: 1 if receipt == "dla" else 0},
                "dla_m": {year: 0},
                "pip_dl": {year: 1 if receipt == "pip" else 0},
                "pip_m": {year: 0},
                "armed_forces_independence_payment": {year: 0},
                "receives_highest_dla_sc": {year: False},
                "receives_enhanced_pip_dl": {year: False},
                "is_blind": {year: False},
            }
            members.append(child)
        unit = {
            "members": members,
            "housing_benefit_eligible": {year: True},
            "housing_benefit_family_premium_category": {year: row["category"]},
            "housing_benefit_has_main_phase_esa": {year: row.get("mainphase", False)},
            "benefits_premiums": {year: row.get("adult_premium", 0)},
            "is_uc_entitled": {year: False},
            "council_tax_reduction_relevant_income_based_benefit": {year: False},
        }
        if "pension" in row:
            unit["housing_benefit_pension_age_regulations_apply"] = {
                year: row["pension"]
            }
        benunits[f"u{index}"] = unit
        households[f"h{index}"] = {
            "members": members,
            "country": {year: row["country"]},
        }
    return Simulation(
        situation={"people": people, "benunits": benunits, "households": households},
        scenario=scenario,
    )


def declared_parameters(simulation, year):
    return simulation.tax_benefit_system.parameters(str(year)).gov.dwp.housing_benefit


def family(simulation, year):
    return simulation.calculate("housing_benefit_family_premium", year)


@PROPERTY
@given(
    year=YEARS,
    country=st.sampled_from(COUNTRIES),
    category=st.sampled_from(("NONE", "ORDINARY_PROTECTED")),
    receipt=st.sampled_from(("none", "dla", "pip")),
    mainphase=st.booleans(),
    carer=st.booleans(),
)
@example(
    year=2015,
    country="ENGLAND",
    category="ORDINARY_PROTECTED",
    receipt="dla",
    mainphase=True,
    carer=True,
)
def test_family_premium_adds_to_applicable_amount(
    year, country, category, receipt, mainphase, carer
):
    # A young parent's five-positive case is pre-closure. PIP uses a young
    # person and an adult parent; no implausible 17-year-old parent of a teen.
    age = 17 if year == 2015 and receipt != "pip" else 40
    common = {
        "country": country,
        "age": age,
        "pension": False,
        "receipt": receipt,
        "mainphase": mainphase,
        "adult_premium": 1799.20 if carer and year == 2015 else 0,
    }
    simulation = build(
        [{**common, "category": category}, {**common, "category": "NONE"}], year
    )
    p = declared_parameters(simulation, year)
    ordinary = 52 * p.premiums.family.amount
    expected_family = [
        ordinary if year < 2016 or value != "NONE" else 0
        for value in (category, "NONE")
    ]
    premiums = family(simulation, year)
    assert premiums == pytest.approx(expected_family, abs=PENNY, rel=0)
    personal = 52 * (
        p.allowances.lone_parent.younger
        if age == 17
        else p.allowances.lone_parent.older
    )
    child = 52 * p.premiums.disabled_child if receipt != "none" else 0
    esa = (
        52 * (p.allowances.lone_parent.older - p.allowances.lone_parent.younger)
        if mainphase and age == 17
        else 0
    )
    assert simulation.calculate(
        "housing_benefit_child_disability_premiums", year
    ) == pytest.approx([child, child], abs=PENNY, rel=0)
    assert simulation.calculate(
        "housing_benefit_main_phase_esa_allowance_adjustment", year
    ) == pytest.approx([esa, esa], abs=PENNY, rel=0)
    amount = simulation.calculate("housing_benefit_applicable_amount", year)
    expected = [
        personal + common["adult_premium"] + value + child + esa
        for value in expected_family
    ]
    assert amount == pytest.approx(expected, abs=PENNY, rel=0)
    assert amount[0] - amount[1] == pytest.approx(
        expected_family[0] - expected_family[1], abs=PENNY, rel=0
    )
    if year >= 2016:
        assert amount[0] - amount[1] == pytest.approx(premiums[0], abs=PENNY, rel=0)
    if year == 2015 and mainphase and carer and receipt == "dla":
        assert all(
            term > 0
            for term in (personal, common["adult_premium"], ordinary, child, esa)
        )


@PROPERTY
@given(
    year=YEARS,
    category=st.sampled_from(CATEGORIES),
    country=st.sampled_from(COUNTRIES),
    children=st.integers(min_value=1, max_value=4),
    lone=st.booleans(),
    pension=st.booleans(),
)
def test_one_premium_per_family(year, category, country, children, lone, pension):
    common = {
        "category": category,
        "country": country,
        "lone": lone,
        "pension": pension,
        "age": 75 if pension else 60,
    }
    simulation = build(
        [{**common, "children": 1}, {**common, "children": children}], year
    )
    first, several = family(simulation, year)
    assert several == first


@PROPERTY
@given(
    year=YEARS,
    country=st.sampled_from(COUNTRIES),
    children=st.integers(min_value=0, max_value=4),
    pension=st.booleans(),
)
def test_no_included_child_has_no_family_premium(year, country, children, pension):
    # Explicit excluded-dependant facts isolate the legal inclusion indicator.
    rows = [
        {
            "category": category,
            "country": country,
            "children": children,
            "included": False,
            "pension": pension,
            "age": 75 if pension else 60,
        }
        for category in CATEGORIES
    ]
    assert family(build(rows, year), year) == pytest.approx([0, 0, 0], abs=0, rel=0)


@PROPERTY
@given(year=YEARS)
@example(year=2015)
@example(year=2016)
@example(year=2030)
def test_family_premium_closure_and_categories(year):
    rows = [
        {"category": category, "country": country, "lone": False, "pension": False}
        for country, category in product(COUNTRIES, CATEGORIES)
    ]
    simulation = build(rows, year)
    ordinary = 52 * declared_parameters(simulation, year).premiums.family.amount
    expected = [
        ordinary if year == 2015 or row["category"] != "NONE" else 0 for row in rows
    ]
    assert family(simulation, year) == pytest.approx(expected, abs=PENNY, rel=0)


@PROPERTY
@given(year=YEARS)
@example(year=2015)
@example(year=2016)
@example(year=2026)
@example(year=2030)
def test_historical_lone_parent_rate_is_limited_to_working_age_lone_parents(year):
    # All 24 category/current-LP/regime/country cells are input-routing
    # contracts. A historical label alone does not adjudicate continuity.
    rows = [
        {
            "category": category,
            "lone": lone,
            "pension": pension,
            "country": country,
            "age": 75 if pension else 60,
        }
        for country, category, lone, pension in product(
            COUNTRIES, CATEGORIES, (False, True), (False, True)
        )
    ]
    simulation = build(rows, year)
    p = declared_parameters(simulation, year).premiums.family
    ordinary, historical = 52 * p.amount, 52 * p.lone_parent_protected_amount
    expected = []
    for row in rows:
        if row["category"] == "NONE" and year >= 2016:
            expected.append(0)
        elif (
            row["category"] == "HISTORICAL_LONE_PARENT_PROTECTED"
            and row["lone"]
            and not row["pension"]
        ):
            expected.append(historical)
        else:
            expected.append(ordinary)
    assert family(simulation, year) == pytest.approx(expected, abs=PENNY, rel=0)
    # No ESA-component fact is supplied for historical higher-rate routing:
    # the saved entitlement conditions exclude that combination.
    assert not simulation.calculate("housing_benefit_has_main_phase_esa", year).any()


@PROPERTY
@given(
    year=YEARS,
    category=st.sampled_from(CATEGORIES),
    country=st.sampled_from(COUNTRIES),
    lone=st.booleans(),
    pension=st.booleans(),
    included=st.booleans(),
)
def test_family_premium_is_within_its_three_supported_amounts(
    year, category, country, lone, pension, included
):
    simulation = build(
        [
            {
                "category": category,
                "country": country,
                "lone": lone,
                "pension": pension,
                "included": included,
                "age": 75 if pension else 60,
            }
        ],
        year,
    )
    p = declared_parameters(simulation, year).premiums.family
    choices = (0, 52 * p.amount, 52 * p.lone_parent_protected_amount)
    actual = family(simulation, year)[0]
    assert any(actual == pytest.approx(value, abs=PENNY, rel=0) for value in choices)
    # Do not impose ordinary <= historical on uprated/projected parameters.


@PROPERTY
@given(
    children=st.integers(min_value=1, max_value=4),
    lone=st.booleans(),
    pension=st.booleans(),
)
def test_northern_ireland_closure_is_independently_reformable(children, lone, pension):
    for year in (2016, 2017):
        rows = [
            {
                "category": "NONE",
                "country": country,
                "children": children,
                "lone": lone,
                "pension": pension,
                "age": 75 if pension else 60,
            }
            for country in COUNTRIES
        ]
        baseline = build(rows, year)
        reformed = build(
            rows,
            year,
            scenario=Scenario(
                parameter_changes={
                    "gov.dwp.housing_benefit.premiums.family.new_claim_end.northern_ireland": {
                        str(year): 20170905
                    }
                }
            ),
        )
        before = declared_parameters(baseline, year).premiums.family
        after = declared_parameters(reformed, year).premiums.family
        assert after.amount == before.amount
        assert after.lone_parent_protected_amount == before.lone_parent_protected_amount
        assert (
            after.new_claim_end.great_britain
            == before.new_claim_end.great_britain
            == 20160501
        )
        assert after.new_claim_end.northern_ireland == 20170905
        assert family(baseline, year) == pytest.approx([0, 0], abs=0, rel=0)
        expected_ni = 52 * before.amount if year == 2016 else 0
        assert family(reformed, year) == pytest.approx(
            [0, expected_ni], abs=PENNY, rel=0
        )
