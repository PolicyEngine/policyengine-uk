"""A published observation remains a fixed-vintage reference, not a take-up rule."""

from pathlib import Path

import pytest
from policyengine_core.errors import ParameterNotFoundError
from policyengine_core.parameters import ParameterNode

from policyengine_uk import CountryTaxBenefitSystem


PARAMETER_PATH = "gov.dwp.ESA.income.takeup_estimate_fye_2019"


@pytest.fixture(scope="module")
def raw_parameters():
    return ParameterNode(
        directory_path=str(Path(__file__).resolve().parents[1] / "parameters")
    )


@pytest.fixture(scope="module")
def uk_system():
    return CountryTaxBenefitSystem()


@pytest.mark.parametrize("date", ["2020-10-29", "2026-01-01"])
def test_joint_benchmark_is_available_at_publication_and_retains_its_vintage(
    raw_parameters, uk_system, date
):
    # ISESA1 C41 is caseload take-up: not ISESA2 expenditure (0.94),
    # nor the current-claimant Income Support factor (1).
    assert raw_parameters.get_child(PARAMETER_PATH)(date) == 0.90
    assert uk_system.parameters.get_child(PARAMETER_PATH)(date) == 0.90
    assert (
        uk_system.get_parameters_at_instant(
            date
        ).gov.dwp.ESA.income.takeup_estimate_fye_2019
        == 0.90
    )


@pytest.mark.parametrize("date", ["2015-01-01", "2020-10-28"])
def test_benchmark_is_unavailable_before_publication(raw_parameters, uk_system, date):
    for parameters in (raw_parameters, uk_system.parameters):
        benchmark = parameters.get_child(PARAMETER_PATH)
        assert benchmark(date) is None
        with pytest.raises(ParameterNotFoundError):
            parameters(date).gov.dwp.ESA.income.takeup_estimate_fye_2019


def test_benchmark_metadata_identifies_the_joint_historical_population(raw_parameters):
    metadata = raw_parameters.get_child(PARAMETER_PATH).metadata

    assert metadata["unit"] == "/1"
    assert metadata["observation_period"] == "FYE 2019"
    assert metadata["publication_date"] == "2020-10-29"
    assert metadata["geography"] == "Great Britain"
    assert metadata["population"] == "eligible families in private households"
    assert metadata["benefits"] == ["income_support", "income_related_esa"]
    assert metadata["measure"] == "caseload"
    assert metadata["confidence_interval"] == {
        "level": 0.95,
        "lower": 0.89,
        "upper": 0.92,
    }


def test_current_income_support_factor_is_unchanged(uk_system):
    assert uk_system.parameters.gov.dwp.income_support.takeup("2026-01-01") == 1
