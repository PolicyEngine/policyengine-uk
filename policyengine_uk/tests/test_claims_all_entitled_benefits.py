"""Regression tests for `claims_all_entitled_benefits`.

The flag is a benefit-unit attribute: a family that reports under £1 in total
across the seven means-tested benefits the formula checks is assumed to claim
everything it is entitled to, and a family that reports £1 or more is assumed
to have reported completely. The formula used to sum the seven reported columns over the whole
simulation (`add(...).sum() < 1`), so in microdata it was False for every
benefit unit as soon as any benefit unit reported any of them, and the
consumers that gate on it collapsed to reporters only. Council Tax Reduction
and Housing Benefit have reporters-only defaults on data-built simulations
(d1390 and d1455); hand-entered situations keep the per-family flag.
"""

import numpy as np
import pandas as pd
import pytest
from hypothesis import example, given, settings, strategies as st

from policyengine_uk import Microsimulation, Simulation
from policyengine_uk.data import UKMultiYearDataset, UKSingleYearDataset

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

YEAR = 2026

SEVEN_REPORTED = [
    "child_tax_credit_reported",
    "working_tax_credit_reported",
    "universal_credit_reported",
    "housing_benefit_reported",
    "jsa_income_reported",
    "income_support_reported",
    "esa_income_reported",
]


def person(reported_uc=0, reported_ctr=0):
    return {
        "age": {YEAR: 40},
        "universal_credit_reported": {YEAR: reported_uc},
        "council_tax_benefit_reported": {YEAR: reported_ctr},
    }


def single_household(reported_uc):
    """One person, one benefit unit, one household — the calculator path."""
    return {
        "people": {"a": person(reported_uc)},
        "benunits": {"bu_a": {"members": ["a"]}},
        "households": {"hh_a": {"members": ["a"]}},
    }


def separate_households(reported_uc_a, reported_uc_b):
    """Two benefit units in two households; `a` is index 0, `b` index 1."""
    return {
        "people": {"a": person(reported_uc_a), "b": person(reported_uc_b)},
        "benunits": {"bu_a": {"members": ["a"]}, "bu_b": {"members": ["b"]}},
        "households": {"hh_a": {"members": ["a"]}, "hh_b": {"members": ["b"]}},
    }


def shared_household(reported_uc_a, reported_uc_b):
    """Two benefit units sharing one household (e.g. a parent and an adult child)."""
    return {
        "people": {"a": person(reported_uc_a), "b": person(reported_uc_b)},
        "benunits": {"bu_a": {"members": ["a"]}, "bu_b": {"members": ["b"]}},
        "households": {"hh": {"members": ["a", "b"]}},
    }


class TestPerBenefitUnit:
    def test_one_reporter_does_not_switch_off_the_other_benefit_unit(self):
        sim = Simulation(situation=separate_households(5_000, 0))
        flag = sim.calculate("claims_all_entitled_benefits", YEAR)
        assert flag.tolist() == [False, True]

    def test_per_benefit_unit_within_one_household(self):
        sim = Simulation(situation=shared_household(5_000, 0))
        flag = sim.calculate("claims_all_entitled_benefits", YEAR)
        assert flag.tolist() == [False, True]

    def test_situation_ctr_default_follows_each_familys_flag(self):
        sim = Simulation(situation=separate_households(5_000, 0))
        would_claim = sim.calculate("would_claim_council_tax_reduction", YEAR)
        assert would_claim.tolist() == [False, True]

    def test_reported_ctr_still_claims_when_the_flag_is_false(self):
        situation = separate_households(5_000, 0)
        situation["people"]["a"] = person(reported_uc=5_000, reported_ctr=800)
        sim = Simulation(situation=situation)
        assert sim.calculate("claims_all_entitled_benefits", YEAR).tolist() == [
            False,
            True,
        ]
        assert sim.calculate("would_claim_council_tax_reduction", YEAR).tolist() == [
            True,
            True,
        ]

    def test_reporters_of_any_of_the_seven_are_false(self):
        for variable in SEVEN_REPORTED:
            situation = separate_households(0, 0)
            situation["people"]["a"][variable] = {YEAR: 100}
            sim = Simulation(situation=situation)
            flag = sim.calculate("claims_all_entitled_benefits", YEAR)
            assert flag.tolist() == [False, True], variable

    def test_single_benefit_unit_semantics_unchanged(self):
        none_reported = Simulation(situation=single_household(0))
        assert none_reported.calculate(
            "claims_all_entitled_benefits", YEAR
        ).tolist() == [True]
        reporter = Simulation(situation=single_household(5_000))
        assert reporter.calculate("claims_all_entitled_benefits", YEAR).tolist() == [
            False
        ]

    def test_homogeneous_benefit_units_agree(self):
        none_reported = Simulation(situation=separate_households(0, 0))
        assert none_reported.calculate("claims_all_entitled_benefits", YEAR).all()
        both_report = Simulation(situation=separate_households(5_000, 5_000))
        assert not both_report.calculate("claims_all_entitled_benefits", YEAR).any()

    def test_under_one_pound_of_reported_benefits_counts_as_none(self):
        sim = Simulation(situation=separate_households(0.5, 0))
        assert sim.calculate("claims_all_entitled_benefits", YEAR).tolist() == [
            True,
            True,
        ]


@pytest.mark.microsimulation
def test_flag_is_evaluated_per_benefit_unit_in_microdata():
    sim = Microsimulation()
    flag = sim.calculate("claims_all_entitled_benefits", YEAR).values.astype(bool)
    reported = np.zeros(len(flag))
    for variable in SEVEN_REPORTED:
        reported = reported + sim.calculate(variable, YEAR, map_to="benunit").values
    assert np.array_equal(flag, reported < 1)
    # Both values must occur: the old formula returned a single value for all.
    assert flag.any() and (~flag).any()


def mock_dataset(situation):
    """Synthetic post-ingestion MOCK tables using the normal UK data schema."""
    tables = {}
    person_ids = {name: i + 1 for i, name in enumerate(situation["people"])}
    memberships = {}
    for plural, entity in (
        ("people", "person"),
        ("benunits", "benunit"),
        ("households", "household"),
    ):
        rows = []
        for index, (_, inputs) in enumerate(situation[plural].items(), start=1):
            row = {f"{entity}_id": index}
            for name, value in inputs.items():
                if name == "members":
                    for member in value:
                        memberships.setdefault(person_ids[member], {})[
                            f"person_{entity}_id"
                        ] = index
                else:
                    row[name] = value[YEAR] if isinstance(value, dict) else value
            rows.append(row)
        tables[entity] = pd.DataFrame(rows).fillna(0)
    for column in ("person_benunit_id", "person_household_id"):
        tables["person"][column] = [
            memberships[person_id][column] for person_id in person_ids.values()
        ]
    return UKMultiYearDataset(
        datasets=[UKSingleYearDataset(**tables, fiscal_year=YEAR)]
    )


def pensioner_households():
    situation = separate_households(0, 0)
    for person_inputs in situation["people"].values():
        person_inputs["age"] = {YEAR: 70}
    for home in situation["households"].values():
        home.update(
            region={YEAR: "NORTH_WEST"},
            tenure_type={YEAR: "RENT_PRIVATELY"},
            rent={YEAR: 8_000},
            council_tax={YEAR: 1_800},
        )
    return situation


@pytest.mark.parametrize("simulation_class", [Simulation, Microsimulation])
@pytest.mark.parametrize(
    "takeup, reported, benefit, expected_award",
    [
        (
            "would_claim_council_tax_reduction",
            "council_tax_benefit_reported",
            "council_tax_reduction",
            1_800,
        ),
        (
            "would_claim_housing_benefit",
            "housing_benefit_reported",
            "housing_benefit",
            8_000,
        ),
    ],
)
def test_mock_data_takeup_is_reporters_only(
    simulation_class, takeup, reported, benefit, expected_award
):
    situation = pensioner_households()
    situation["people"]["b"][reported] = {YEAR: 100}
    simulation = simulation_class(dataset=mock_dataset(situation))
    assert simulation.calculate(takeup, YEAR).tolist() == [False, True]
    np.testing.assert_allclose(simulation.calculate(benefit, YEAR), [0, expected_award])
    # The non-reporter is entitled: an explicit input enables its award.
    for family in situation["benunits"].values():
        family[takeup] = {YEAR: True}
    explicit = simulation_class(dataset=mock_dataset(situation))
    np.testing.assert_allclose(
        explicit.calculate(benefit, YEAR), [expected_award, expected_award]
    )


def test_hand_entered_housing_benefit_keeps_main_takeup():
    simulation = Simulation(situation=pensioner_households())
    assert simulation.calculate("would_claim_housing_benefit", YEAR).tolist() == [
        True,
        True,
    ]
    np.testing.assert_allclose(
        simulation.calculate("housing_benefit", YEAR), [8_000, 8_000]
    )


@pytest.mark.parametrize(
    "reported",
    [
        "pension_credit_reported",
        "child_benefit_reported",
        "council_tax_benefit_reported",
    ],
)
def test_reports_outside_the_seven_leave_the_all_benefits_flag_true(reported):
    situation = separate_households(0, 0)
    situation["people"]["a"][reported] = {YEAR: 100}
    simulation = Simulation(situation=situation)
    assert simulation.calculate("claims_all_entitled_benefits", YEAR).tolist() == [
        True,
        True,
    ]


# Each generated family is independently eligible or ineligible and may have
# reported CTR. No explicit take-up column is supplied; other families cannot enable it.
CTR_FAMILIES = st.lists(
    st.tuples(
        st.integers(min_value=18, max_value=90),
        st.sampled_from(("ENGLAND", "SCOTLAND", "WALES")),
        st.integers(min_value=0, max_value=50_000),
        st.integers(min_value=0, max_value=50_000),
        st.booleans(),
        st.sampled_from((0, 100)),
    ),
    min_size=1,
    max_size=4,
)


@given(families=CTR_FAMILIES)
@example(families=[(40, "SCOTLAND", 0, 0, True, 0)])
@example(
    families=[
        (40, "WALES", 0, 0, True, 0),
        (40, "WALES", 0, 0, True, 100),
        (70, "ENGLAND", 0, 0, False, 100),
    ]
)
@settings(max_examples=30, deadline=None)
def test_ctr_is_zero_for_every_nonreporter_without_an_explicit_claim_flag(families):
    situation = {"people": {}, "benunits": {}, "households": {}}
    must_be_zero = []
    councils = {
        "ENGLAND": "MAIDSTONE",
        "SCOTLAND": "CITY_OF_EDINBURGH",
        "WALES": "CARDIFF",
    }
    for index, (age, country, income, savings, claims_all, reported) in enumerate(
        families
    ):
        name = f"person_{index}"
        situation["people"][name] = {
            "age": {YEAR: age},
            "employment_income": {YEAR: income},
            "council_tax_benefit_reported": {YEAR: reported},
        }
        benunit = {
            "members": [name],
            "claims_all_entitled_benefits": {YEAR: claims_all},
            "would_claim_uc": {YEAR: False},
        }
        situation["benunits"][f"bu_{index}"] = benunit
        situation["households"][f"hh_{index}"] = {
            "members": [name],
            "country": {YEAR: country},
            "local_authority": {YEAR: councils[country]},
            "council_tax": {YEAR: 1_800},
            "savings": {YEAR: savings},
        }
        must_be_zero.append(reported == 0)
    sim = Simulation(dataset=mock_dataset(situation))
    mask = np.array(must_be_zero, dtype=bool)
    assert not sim.calculate("would_claim_council_tax_reduction", YEAR)[mask].any()
    for variable in (
        "simulated_council_tax_reduction_benunit",
        "council_tax_benefit",
        "council_tax_reduction",
    ):
        assert (sim.calculate(variable, YEAR)[mask] == 0).all(), variable
