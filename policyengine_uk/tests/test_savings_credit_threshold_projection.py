import pytest

from policyengine_uk import system
from policyengine_uk.parameters.gov.dwp.pension_credit.create_savings_credit_threshold_projection import (
    project_maximum_savings_credit,
    round_currency,
    savings_credit_threshold,
)


def _parameters():
    return system.parameters


@pytest.mark.parametrize(
    ("relationship", "base_maximum", "expected_2027_maximum"),
    [
        ("SINGLE", 17.96, 18.3400336),
        ("COUPLE", 20.10, 20.525316),
    ],
)
def test_2027_threshold_preserves_the_cpi_projected_maximum(
    relationship,
    base_maximum,
    expected_2027_maximum,
):
    """DWP A14/2025 sets £17.96/£20.10 and a 3.8% enacted CPI rise.

    The first forecast uses the repository's 2.116% September 2026 CPI input.
    """
    parameters = _parameters()
    savings_credit = parameters.gov.dwp.pension_credit.savings_credit
    guarantee = parameters.gov.dwp.pension_credit.guarantee_credit.minimum_guarantee
    phase_in_rate = float(savings_credit.rate.phase_in("2027-04-01"))
    projected_guarantee = float(getattr(guarantee, relationship)("2027-04-01"))
    projected_threshold = float(
        getattr(savings_credit.threshold, relationship)("2027-04-01")
    )
    projected_maximum = phase_in_rate * (projected_guarantee - projected_threshold)

    assert base_maximum * 1.02116 == pytest.approx(expected_2027_maximum)
    assert projected_maximum == pytest.approx(expected_2027_maximum)


def test_projected_thresholds_preserve_the_maximum_in_every_forecast_year():
    parameters = _parameters()
    savings_credit = parameters.gov.dwp.pension_credit.savings_credit
    guarantee = parameters.gov.dwp.pension_credit.guarantee_credit.minimum_guarantee
    cpi = parameters.gov.economic_assumptions.statutory_uprating_inputs.cpi_september

    for relationship in ("SINGLE", "COUPLE"):
        guarantee_parameter = getattr(guarantee, relationship)
        threshold_parameter = getattr(savings_credit.threshold, relationship)
        base_phase_in_rate = float(savings_credit.rate.phase_in("2026-04-01"))
        maximum = round_currency(
            base_phase_in_rate
            * (
                float(guarantee_parameter("2026-04-01"))
                - float(threshold_parameter("2026-04-01"))
            )
        )
        for year in range(2027, 2040):
            maximum = project_maximum_savings_credit(
                maximum,
                float(cpi(f"{year - 1}-09-01")),
            )
            phase_in_rate = float(savings_credit.rate.phase_in(f"{year}-04-01"))
            actual = phase_in_rate * (
                float(guarantee_parameter(f"{year}-04-01"))
                - float(threshold_parameter(f"{year}-04-01"))
            )
            assert actual == pytest.approx(maximum), (relationship, year)


def test_projection_floors_cpi_and_validates_the_phase_in_rate():
    assert project_maximum_savings_credit(17.96, -0.02) == 17.96
    assert savings_credit_threshold(238, 17.96, 0.6) == pytest.approx(208.0666666667)
    with pytest.raises(ValueError, match="must be positive"):
        savings_credit_threshold(238, 17.96, 0)
