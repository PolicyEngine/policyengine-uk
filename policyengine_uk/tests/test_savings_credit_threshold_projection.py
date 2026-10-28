import pytest
from policyengine_core.periods import instant

from policyengine_uk import Simulation, system
from policyengine_uk.model_api import Scenario
from policyengine_uk.parameters.gov.dwp.pension_credit.savings_credit.create_savings_credit_threshold import (
    project_maximum_savings_credit,
    round_currency,
    savings_credit_threshold,
)
from policyengine_uk.parameters.gov.dwp.pension_credit.pension_age_projection_base import (
    projection_base_year,
)
from policyengine_uk.tax_benefit_system import (
    CountryTaxBenefitSystem,
    process_parameter_tree,
)


PENSIONER = {
    "people": {"person": {"age": {2027: 70}}},
    "benunits": {"benunit": {"members": ["person"]}},
    "households": {"household": {"members": ["person"]}},
}


def _parameters():
    return system.parameters


def _raw_parameters():
    tax_benefit_system = CountryTaxBenefitSystem()
    tax_benefit_system.reset_parameters()
    return tax_benefit_system.parameters


@pytest.mark.parametrize(
    ("relationship", "base_maximum", "expected_2027_maximum"),
    [
        ("SINGLE", 17.96, 18.5886),
        ("COUPLE", 20.10, 20.8035),
    ],
)
def test_2027_threshold_preserves_the_cpi_projected_maximum(
    relationship,
    base_maximum,
    expected_2027_maximum,
):
    """DWP A14/2025 sets £17.96/£20.10 and a 3.8% enacted CPI rise.

    The first forecast uses September 2026 CPI, 3.5% (ONS, 21 October 2026).
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

    assert base_maximum * 1.035 == pytest.approx(expected_2027_maximum)
    assert projected_maximum == pytest.approx(expected_2027_maximum, abs=0.001)


def test_projected_thresholds_preserve_the_maximum_in_every_forecast_year():
    parameters = _parameters()
    savings_credit = parameters.gov.dwp.pension_credit.savings_credit
    guarantee = parameters.gov.dwp.pension_credit.guarantee_credit.minimum_guarantee
    cpi = parameters.gov.economic_assumptions.indices.september_cpi_uprating

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
                float(cpi(f"{year}-04-01")) / float(cpi(f"{year - 1}-04-01")) - 1,
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


# A next year's rates update, entered for every parameter the pension-age
# projections start from (illustrative amounts, not enacted rates).
NEXT_YEAR_RATES = {
    "gov.dwp.pension_credit.guarantee_credit.minimum_guarantee.SINGLE": 250,
    "gov.dwp.pension_credit.guarantee_credit.minimum_guarantee.COUPLE": 380,
    "gov.dwp.pension_credit.savings_credit.threshold.SINGLE": 220,
    "gov.dwp.pension_credit.savings_credit.threshold.COUPLE": 350,
    "gov.dwp.housing_benefit.allowances.single.aged": 270,
    "gov.dwp.housing_benefit.allowances.lone_parent.aged": 270,
    "gov.dwp.housing_benefit.allowances.couple.aged": 405,
}


def _system_with_rates(rates, year=2027):
    """Process an edited raw YAML fixture, rather than a runtime modifier."""
    tax_benefit_system = CountryTaxBenefitSystem()
    tax_benefit_system.reset_parameters()
    for path, value in rates.items():
        tax_benefit_system.parameters.get_child(path).update(
            start=instant(f"{year}-04-01"), stop=None, value=value
        )
    raw = tax_benefit_system.parameters
    # Later reforms of this fixture must retain its complete enacted base.
    tax_benefit_system._enacted_parameters = raw.clone()
    tax_benefit_system._raw_parameters = raw.clone()
    (
        tax_benefit_system.parameters,
        tax_benefit_system._projected_timelines,
    ) = process_parameter_tree(raw)
    return tax_benefit_system


def test_projection_base_year_is_the_last_enacted_year():
    assert projection_base_year(_raw_parameters()) == 2026


def test_next_year_rates_move_the_projection_base():
    """Once 2027-28 rates are entered, the projections start from them: the
    maximum Savings Credit follows CPI from the enacted 2027 maximum, and each
    entered value is exact and anchors later years."""
    parameters = _system_with_rates(NEXT_YEAR_RATES).parameters
    savings_credit = parameters.gov.dwp.pension_credit.savings_credit
    guarantee = parameters.gov.dwp.pension_credit.guarantee_credit.minimum_guarantee
    cpi = parameters.gov.economic_assumptions.indices.september_cpi_uprating
    for path, value in NEXT_YEAR_RATES.items():
        assert parameters.get_child(path)("2027-06-01") == value, path

    for relationship, maximum in (("SINGLE", 18.0), ("COUPLE", 18.0)):
        # 0.6 x (250 - 220) and 0.6 x (380 - 350).
        threshold = getattr(savings_credit.threshold, relationship)
        index = getattr(savings_credit.threshold_uprating, relationship)
        assert index("2027-04-30") == 1
        projected_maximum = maximum * (
            1 + max(float(cpi("2028-04-01")) / float(cpi("2027-04-01")) - 1, 0)
        )
        phase_in = float(savings_credit.rate.phase_in("2028-04-30"))
        assert phase_in * (
            float(getattr(guarantee, relationship)("2028-04-30"))
            - float(threshold("2028-04-30"))
        ) == pytest.approx(projected_maximum)
    protected = (
        parameters.gov.dwp.housing_benefit.allowances.protected_pension_age_uprating
    )
    for name in ("single", "lone_parent", "couple"):
        assert getattr(protected, name)("2027-04-30") == 1


@pytest.mark.parametrize(
    "path",
    [
        "gov.dwp.pension_credit.guarantee_credit.minimum_guarantee.SINGLE",
        "gov.dwp.pension_credit.savings_credit.threshold.SINGLE",
        "gov.dwp.housing_benefit.allowances.lone_parent.aged",
    ],
)
def test_rates_update_that_misses_a_parameter_raises(path):
    """A 2027 rate for some of the base parameters and not others would build
    the indices from a projected amount, so the update must be completed."""
    with pytest.raises(ValueError, match="enacted to the same year"):
        _system_with_rates({path: NEXT_YEAR_RATES[path]})


@pytest.mark.parametrize("relationship", ["SINGLE", "COUPLE"])
def test_threshold_uses_generated_index_through_standard_uprating(relationship):
    savings_credit = _parameters().gov.dwp.pension_credit.savings_credit
    threshold = getattr(savings_credit.threshold, relationship)

    assert threshold.metadata["uprating"] == (
        f"gov.dwp.pension_credit.savings_credit.threshold_uprating.{relationship}"
    )
