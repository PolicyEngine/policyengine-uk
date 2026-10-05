"""Tests for the 2020 over-75 TV licence concession transition."""

from pathlib import Path

import pytest
from policyengine_core.parameters import ParameterNode

import policyengine_uk
from policyengine_uk import CountryTaxBenefitSystem


def _requirement(parameter_root):
    return parameter_root.gov.dcms.bbc.tv_licence.discount.aged.must_claim_pc


def test_pension_credit_condition_uses_the_statutory_start_date():
    """The BBC deferred the condition from 1 June to 1 August 2020."""
    parameters = ParameterNode(
        directory_path=str(Path(policyengine_uk.__file__).parent / "parameters")
    )
    requirement = _requirement(parameters)

    assert requirement("2020-07-31") == 0
    assert requirement("2020-08-01") == 1


def test_pension_credit_condition_is_annualised_across_2020_21():
    """The fiscal year has 117 unrestricted and 248 restricted days."""
    system = CountryTaxBenefitSystem()
    requirement = _requirement(system.get_parameters_at_instant("2020"))

    assert requirement == pytest.approx(248 / 365)
