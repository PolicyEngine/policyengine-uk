import pytest
from policyengine_core.periods import instant

from policyengine_uk import Simulation, system
from policyengine_uk.model_api import Scenario
from policyengine_uk.parameters.gov.dwp.pension_credit.create_savings_credit_threshold_projection import (
    project_maximum_savings_credit,
    round_currency,
    savings_credit_threshold,
)
from policyengine_uk.tax_benefit_system import CountryTaxBenefitSystem


PENSIONER = {
    "people": {"person": {"age": {2027: 70}}},
    "benunits": {"benunit": {"members": ["person"]}},
    "households": {"household": {"members": ["person"]}},
}


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


@pytest.mark.parametrize(
    ("relationship", "reformed_value"),
    [("SINGLE", 100), ("COUPLE", 200)],
)
def test_preprocessing_threshold_reform_is_not_replaced_by_projection(
    relationship,
    reformed_value,
):
    """Generated indices must not overwrite scenario parameter changes."""
    path = f"gov.dwp.pension_credit.savings_credit.threshold.{relationship}"
    simulation = Simulation(
        situation=PENSIONER,
        scenario=Scenario(
            parameter_changes={path: {"2027": reformed_value}},
            applied_before_data_load=True,
        ),
    )
    threshold = simulation.tax_benefit_system.parameters.get_child(path)

    assert threshold("2027-06-01") == reformed_value


def test_postprocessing_threshold_reform_is_not_replaced_by_projection():
    """The direct reform interface must preserve its explicit value too."""
    path = "gov.dwp.pension_credit.savings_credit.threshold.SINGLE"
    simulation = Simulation(
        situation=PENSIONER,
        reform={path: {"2027": 100}},
    )
    threshold = simulation.tax_benefit_system.parameters.get_child(path)

    assert threshold("2027-06-01") == 100


def test_future_explicit_threshold_is_the_uprating_anchor():
    """A later source value remains exact and anchors subsequent forecasts."""
    tax_benefit_system = CountryTaxBenefitSystem()
    tax_benefit_system.reset_parameters()
    savings_credit = tax_benefit_system.parameters.gov.dwp.pension_credit.savings_credit
    savings_credit.threshold.SINGLE.update(
        start=instant("2027-04-01"),
        stop=None,
        value=100,
    )

    tax_benefit_system.process_parameters()
    savings_credit = tax_benefit_system.parameters.gov.dwp.pension_credit.savings_credit
    threshold = savings_credit.threshold.SINGLE
    index = savings_credit.threshold_uprating.SINGLE

    assert threshold("2027-06-01") == 100
    assert threshold("2028-06-01") == pytest.approx(
        100 * index("2028-06-01") / index("2027-06-01")
    )


@pytest.mark.parametrize("relationship", ["SINGLE", "COUPLE"])
def test_threshold_uses_generated_index_through_standard_uprating(relationship):
    savings_credit = _parameters().gov.dwp.pension_credit.savings_credit
    threshold = getattr(savings_credit.threshold, relationship)

    assert threshold.metadata["uprating"] == (
        f"gov.dwp.pension_credit.savings_credit.threshold_uprating.{relationship}"
    )
