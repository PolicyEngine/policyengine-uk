"""Tests for the 2020 over-75 TV licence concession transition."""

from pathlib import Path

import pytest
from policyengine_core.parameters import ParameterNode

import policyengine_uk
from policyengine_uk import CountryTaxBenefitSystem, Simulation
from policyengine_uk.utils.excise import fiscal_year_segments


def _requirement(parameter_root):
    return parameter_root.gov.dcms.bbc.tv_licence.discount.aged.must_claim_pc


def test_pension_credit_condition_uses_the_statutory_start_date():
    """The BBC deferred the condition from 1 June to 1 August 2020."""
    parameters = ParameterNode(
        directory_path=str(Path(policyengine_uk.__file__).parent / "parameters")
    )
    requirement = _requirement(parameters)

    assert requirement("2020-07-31") is False
    assert requirement("2020-08-01") is True


def test_pension_credit_condition_keeps_its_date_after_processing():
    """Processing preserves the 1 August Boolean policy transition."""
    system = CountryTaxBenefitSystem()
    requirement = _requirement(system.parameters)

    assert requirement("2020-07-31") is False
    assert requirement("2020-08-01") is True


def test_pension_credit_condition_segments_the_2020_21_fiscal_year():
    """The fiscal year has 117 unrestricted and 248 restricted days."""
    system = CountryTaxBenefitSystem()
    aged_rules = system.parameters.gov.dcms.bbc.tv_licence.discount.aged
    segments = list(fiscal_year_segments(aged_rules, 2020))

    unrestricted_share = sum(
        share for rules, share in segments if not rules.must_claim_pc
    )
    restricted_share = sum(share for rules, share in segments if rules.must_claim_pc)

    assert unrestricted_share == pytest.approx(117 / 365)
    assert restricted_share == pytest.approx(248 / 365)
    assert all(isinstance(rules.must_claim_pc, bool) for rules, _ in segments)


def test_year_keyed_minimum_age_reform_applies_to_one_fiscal_year():
    """A bare-year age reform must not be split across adjacent years."""
    years = (2024, 2025, 2026)
    situation = {
        "people": {
            "person": {
                "age": {str(year): 72 for year in years},
            },
        },
        "benunits": {
            "benunit": {
                "members": ["person"],
                "pension_credit": {str(year): 1 for year in years},
            },
        },
        "households": {
            "household": {
                "members": ["person"],
            },
        },
    }
    reform = {
        "gov.dcms.bbc.tv_licence.discount.aged.min_age": {"2025": 70},
    }
    simulation = Simulation(situation=situation, reform=reform)

    discounts = [simulation.calculate("tv_licence_discount", year)[0] for year in years]

    assert discounts == pytest.approx([0, 1, 0])
