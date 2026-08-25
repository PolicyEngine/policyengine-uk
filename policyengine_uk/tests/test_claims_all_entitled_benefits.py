"""Regression tests for `claims_all_entitled_benefits`.

The flag is a benefit-unit attribute: a family that reports none of the seven
means-tested benefits the formula checks is assumed to claim everything it is
entitled to, and a family that reports any of them is assumed to have reported
completely. The formula used to sum the seven reported columns over the whole
simulation (`add(...).sum() < 1`), so in microdata it was False for every
benefit unit as soon as any benefit unit reported any of them, and the
consumers that gate on it (`would_claim_council_tax_reduction` above all)
collapsed to FRS reporters only.
"""

import numpy as np
import pytest

from policyengine_uk import Microsimulation, Simulation

YEAR = 2025

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

    def test_would_claim_council_tax_reduction_follows_the_flag(self):
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
