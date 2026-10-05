import pytest

from policyengine_uk import system
from policyengine_uk.parameters.gov.dwp.housing_benefit.allowances.create_protected_pension_age_uprating import (
    BASE_ALLOWANCE,
    GUARANTEE_COMPONENT,
    SAVINGS_CREDIT_COMPONENT,
    project_components,
)


def _parameters():
    return system.parameters


def test_protected_allowance_index_combines_the_two_statutory_inputs():
    parameters = _parameters()
    inputs = parameters.gov.economic_assumptions.statutory_uprating_inputs
    index = parameters.gov.dwp.housing_benefit.allowances.protected_pension_age_uprating

    guarantee, savings_credit_uplift = project_components(
        GUARANTEE_COMPONENT,
        SAVINGS_CREDIT_COMPONENT,
        inputs.awe_total_pay_may_july("2026-07-01"),
        inputs.cpi_september("2026-09-01"),
    )

    assert inputs.awe_total_pay_may_july("2026-07-01") == pytest.approx(0.039)
    assert inputs.cpi_september("2026-09-01") == pytest.approx(0.02116)
    assert index("2026-04-01") == 1
    expected_index = (guarantee + savings_credit_uplift) / BASE_ALLOWANCE
    assert expected_index == pytest.approx(1.037745625)
    assert index("2027-04-01") == pytest.approx(expected_index)


def test_single_and_lone_parent_use_the_composite_projection():
    allowances = _parameters().gov.dwp.housing_benefit.allowances
    index = allowances.protected_pension_age_uprating
    expected_2027 = 256 * index("2027-04-01") / index("2026-04-01")

    assert allowances.single.aged("2026-04-01") == 256
    assert allowances.lone_parent.aged("2026-04-01") == 256
    assert expected_2027 == pytest.approx(265.66288)
    assert allowances.single.aged("2027-04-01") == pytest.approx(expected_2027)
    assert allowances.lone_parent.aged("2027-04-01") == pytest.approx(expected_2027)
    assert allowances.single.aged("2027-04-01") != pytest.approx(
        256
        * _parameters().gov.benefit_uprating_cpi("2027-04-01")
        / _parameters().gov.benefit_uprating_cpi("2026-04-01")
    )


def test_component_projection_does_not_reduce_cash_amounts():
    assert project_components(238, 18, -0.01, -0.02) == (238, 18)
