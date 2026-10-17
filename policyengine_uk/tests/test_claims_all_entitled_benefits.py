"""Regression tests for `claims_all_entitled_benefits`.

The flag is a benefit-unit attribute: a family that reports under £1 in total
across the seven means-tested benefits the formula checks is assumed to claim
everything it is entitled to, and a family that reports £1 or more is assumed
to have reported completely. The formula used to sum the seven reported columns over the whole
simulation (`add(...).sum() < 1`), so in microdata it was False for every
benefit unit as soon as any benefit unit reported any of them, and the
consumers that gate on it collapsed to reporters only. Council Tax Reduction
now has its own explicit reporters-only default until calibrated data take-up
lands (uk-data#448; d1390).
"""

import numpy as np
import pytest
from hypothesis import example, given, settings, strategies as st

from policyengine_uk import Microsimulation, Simulation

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

    def test_ctr_default_does_not_follow_the_all_benefits_flag(self):
        sim = Simulation(situation=separate_households(5_000, 0))
        would_claim = sim.calculate("would_claim_council_tax_reduction", YEAR)
        assert would_claim.tolist() == [False, False]

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
            False,
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


# Each generated family is independently eligible or ineligible and may have
# reported CTR or an explicit take-up input. Other families cannot enable it.
CTR_FAMILIES = st.lists(
    st.tuples(
        st.integers(min_value=18, max_value=90),
        st.sampled_from(("ENGLAND", "SCOTLAND", "WALES")),
        st.integers(min_value=0, max_value=50_000),
        st.integers(min_value=0, max_value=50_000),
        st.booleans(),
        st.sampled_from((None, False, True)),
        st.sampled_from((0, 100)),
    ),
    min_size=1,
    max_size=4,
)


@given(families=CTR_FAMILIES)
@example(families=[(40, "SCOTLAND", 0, 0, True, None, 0)])
@example(
    families=[
        (40, "WALES", 0, 0, True, None, 0),
        (40, "WALES", 0, 0, True, True, 0),
        (70, "ENGLAND", 0, 0, False, None, 100),
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
    for index, (age, country, income, savings, claims_all, flag, reported) in enumerate(
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
        if flag is not None:
            benunit["would_claim_council_tax_reduction"] = {YEAR: flag}
        situation["benunits"][f"bu_{index}"] = benunit
        situation["households"][f"hh_{index}"] = {
            "members": [name],
            "country": {YEAR: country},
            "local_authority": {YEAR: councils[country]},
            "council_tax": {YEAR: 1_800},
            "savings": {YEAR: savings},
        }
        must_be_zero.append(reported == 0 and flag is not True)
    sim = Simulation(situation=situation)
    mask = np.array(must_be_zero, dtype=bool)
    assert not sim.calculate("would_claim_council_tax_reduction", YEAR)[mask].any()
    for variable in (
        "simulated_council_tax_reduction_benunit",
        "council_tax_benefit",
        "council_tax_reduction",
    ):
        assert (sim.calculate(variable, YEAR)[mask] == 0).all(), variable
