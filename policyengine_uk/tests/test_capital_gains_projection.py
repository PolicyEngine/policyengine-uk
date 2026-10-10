"""Projection mechanics on synthetic records, not estimates for the UK population."""

from dataclasses import FrozenInstanceError, replace
import json

import numpy as np
import pandas as pd
import pytest

from policyengine_uk import CountryTaxBenefitSystem, Microsimulation, Simulation
from policyengine_uk.data.capital_gains_projection import (
    CapitalGainsProjection,
    obr_eot_projection,
)
from policyengine_uk.data.dataset_schema import UKMultiYearDataset, UKSingleYearDataset
from policyengine_uk.data.economic_assumptions import extend_single_year_dataset
from policyengine_uk.model_api import Scenario


COMPONENTS = (
    "capital_gains_badr",
    "capital_gains_residential_property",
    "capital_gains_carried_interest",
)
INPUTS = ("capital_gains_before_response", *COMPONENTS)


@pytest.fixture
def projection():
    return CapitalGainsProjection(
        name="synthetic-test-projection",
        base_year=2024,
        annual_growth={2025: 0.10, 2026: 0.20, 2027: -0.10},
        source="Synthetic growth rates for an engineering test",
        vintage="2026-10-10",
        assumptions="Common growth for every gains component; uniform weight growth",
    )


@pytest.fixture
def dataset():
    """One positive gainer, a non-gainer, and a record with a net loss."""
    ids = np.arange(1, 4)
    return UKSingleYearDataset(
        person=pd.DataFrame(
            {
                "person_id": ids,
                "person_benunit_id": ids,
                "person_household_id": ids,
                "age": [45, 45, 45],
                "employment_income": [150_000.0, 0.0, 0.0],
                "capital_gains_before_response": [100_000.0, 0.0, -10_000.0],
                "capital_gains_badr": [10_000.0, 0.0, 0.0],
                "capital_gains_residential_property": [20_000.0, 0.0, 0.0],
                "capital_gains_carried_interest": [5_000.0, 0.0, 0.0],
            }
        ),
        benunit=pd.DataFrame({"benunit_id": ids}),
        household=pd.DataFrame(
            {
                "household_id": ids,
                "household_weight": [2.0, 3.0, 5.0],
                "region": "LONDON",
                "tenure_type": "OWNED_OUTRIGHT",
                "rent": 0.0,
                "council_tax": 0.0,
            }
        ),
        fiscal_year=2024,
    )


def situation_from(dataset):
    year = int(dataset.time_period)
    people, benunits, households = {}, {}, {}
    for i, row in dataset.person.iterrows():
        name = f"person{i}"
        people[name] = {
            variable: {year: float(row[variable])}
            for variable in (*INPUTS, "age", "employment_income")
        }
        benunits[f"benunit{i}"] = {"members": [name]}
        households[f"household{i}"] = {
            "members": [name],
            "household_weight": {
                year: float(dataset.household.iloc[i].household_weight)
            },
        }
    return {"people": people, "benunits": benunits, "households": households}


def aggregate_factor(projection, year):
    return np.prod([1 + growth for y, growth in projection.annual_growth if y <= year])


def population_factor(parameters, base_year, year):
    growth = parameters.gov.economic_assumptions.yoy_growth.ons.population
    return np.prod([1 + growth(y) for y in range(base_year + 1, year + 1)])


def test_projection_is_immutable_and_fingerprint_tracks_content(projection):
    growth = {2026: 0.20, 2025: 0.10, 2027: -0.10}
    equivalent = replace(projection, annual_growth=growth)
    assert equivalent.fingerprint == projection.fingerprint
    assert equivalent.end_year == 2027
    growth[2025] = 0.90
    assert dict(equivalent.annual_growth)[2025] == 0.10
    with pytest.raises(FrozenInstanceError):
        equivalent.vintage = "changed"
    assert (
        replace(projection, vintage="2026-10-11").fingerprint != projection.fingerprint
    )
    assert (
        replace(
            projection, annual_growth={2025: 0.11, 2026: 0.20, 2027: -0.10}
        ).fingerprint
        != projection.fingerprint
    )
    metadata = json.loads(json.dumps(projection.metadata))
    assert metadata["source"] == projection.source
    assert metadata["vintage"] == projection.vintage
    assert metadata["assumptions"] == projection.assumptions


@pytest.mark.parametrize(
    "changes",
    [
        {"annual_growth": {}},
        {"annual_growth": {2026: 0.1}},
        {"annual_growth": {2025: 0.1, 2027: 0.1}},
        {"annual_growth": {2024: 0.1, 2025: 0.1}},
        {"annual_growth": {"2025": 0.1}},
        {"annual_growth": {2025: -1.0}},
        {"annual_growth": {2025: -1.1}},
        {"annual_growth": {2025: float("nan")}},
        {"annual_growth": {2025: float("inf")}},
        {"source": ""},
        {"vintage": " "},
        {"assumptions": ""},
    ],
)
def test_invalid_projection_is_rejected(projection, changes):
    with pytest.raises((TypeError, ValueError)):
        replace(projection, **changes)


def test_obr_candidate_is_explicit_and_has_a_finite_horizon():
    candidate = obr_eot_projection()
    assert candidate.base_year == 2024
    assert candidate.end_year == 2030
    assert dict(candidate.annual_growth) == {
        2025: -0.016,
        2026: 0.234,
        2027: 0.116,
        2028: 0.107,
        2029: 0.102,
        2030: 0.101,
    }
    assert "obr.uk" in candidate.source
    assert "experimental" in json.dumps(candidate.metadata).lower()


def test_default_uprating_retains_gdp_per_capita(dataset):
    simulation = Simulation(situation=situation_from(dataset))
    parameters = simulation.tax_benefit_system.parameters
    index = parameters.gov.economic_assumptions.indices.obr.per_capita.gdp
    expected = (
        dataset.person["capital_gains_before_response"] * index(2026) / index(2024)
    )
    assert simulation.calculate("capital_gains_before_response", 2026) == pytest.approx(
        expected, rel=1e-6
    )
    extended = extend_single_year_dataset(dataset, parameters, end_year=2026)
    growth = parameters.gov.economic_assumptions.yoy_growth.obr.per_capita.gdp
    expected_dataset = dataset.person["capital_gains_before_response"] * np.prod(
        [1 + growth(year) for year in (2025, 2026)]
    )
    np.testing.assert_allclose(
        extended[2026].person["capital_gains_before_response"],
        expected_dataset,
        rtol=1e-6,
    )


def test_parameters_net_aggregate_growth_of_population(projection):
    parameters = CountryTaxBenefitSystem(capital_gains_projection=projection).parameters
    economic = parameters.gov.economic_assumptions
    for year, growth in projection.annual_growth:
        population_growth = economic.yoy_growth.ons.population(year)
        assert economic.yoy_growth.capital_gains(year) == pytest.approx(
            (1 + growth) / (1 + population_growth) - 1
        )
        assert economic.indices.capital_gains(year) / economic.indices.capital_gains(
            projection.base_year
        ) == pytest.approx(
            aggregate_factor(projection, year)
            / population_factor(parameters, projection.base_year, year),
            rel=1e-6,
        )


def test_projection_preserves_observed_inputs_and_does_not_mutate_dataset(
    projection, dataset
):
    original = dataset.copy()
    simulation = Simulation(dataset=dataset, capital_gains_projection=projection)
    for variable in INPUTS:
        assert simulation.calculate(variable, 2024) == pytest.approx(
            original.person[variable]
        )
    for before, after in zip(original.tables, dataset.tables):
        pd.testing.assert_frame_equal(before, after)


def test_direct_and_dataset_projection_agree_and_preserve_component_mix(
    projection, dataset
):
    direct = Simulation(
        situation=situation_from(dataset), capital_gains_projection=projection
    )
    micro = Microsimulation(dataset=dataset, capital_gains_projection=projection)
    for year in (2025, 2026, 2027):
        factor = aggregate_factor(projection, year) / population_factor(
            direct.tax_benefit_system.parameters, 2024, year
        )
        for variable in INPUTS:
            expected = dataset.person[variable] * factor
            assert direct.calculate(variable, year) == pytest.approx(expected, rel=1e-6)
            assert micro.calculate(variable, year, unweighted=True) == pytest.approx(
                expected, rel=1e-6
            )
        # Includes the loss; weighted sums test growth without adding population twice.
        assert micro.calculate("capital_gains_before_response", year).sum() == (
            pytest.approx(150_000 * aggregate_factor(projection, year), rel=1e-6)
        )


def test_supplied_requested_year_gains_override_projection(projection):
    simulation = Simulation(
        situation={
            "capital_gains": {2024: 100_000, 2026: 12_345, 2031: 54_321},
            "capital_gains_badr": {2024: 10_000, 2026: 5_000, 2031: 4_000},
        },
        capital_gains_projection=projection,
    )
    for year, total, badr in ((2026, 12_345, 5_000), (2031, 54_321, 4_000)):
        assert simulation.calculate("capital_gains_before_response", year)[0] == total
        assert simulation.calculate("capital_gains_badr", year)[0] == badr


def test_multi_year_supplied_gains_are_authoritative_beyond_horizon(
    projection, dataset
):
    future = dataset.copy()
    future.time_period = "2031"
    future.person["capital_gains_before_response"] = [45_678.0, 0.0, -123.0]
    simulation = Simulation(
        dataset=UKMultiYearDataset(datasets=[dataset, future]),
        capital_gains_projection=projection,
    )
    assert simulation.calculate("capital_gains_before_response", 2031) == pytest.approx(
        [45_678.0, 0.0, -123.0]
    )


@pytest.mark.parametrize("source_year,target_year", [(2024, 2031), (2023, 2025)])
def test_missing_year_cannot_silently_extend_projection(
    projection, source_year, target_year
):
    simulation = Simulation(
        situation={"capital_gains": {source_year: 100_000}},
        capital_gains_projection=projection,
    )
    with pytest.raises(ValueError):
        simulation.calculate("capital_gains_before_response", target_year)


def test_absent_gains_remain_zero_beyond_projection_horizon(projection):
    simulation = Simulation(situation={"age": 45}, capital_gains_projection=projection)
    for variable in INPUTS:
        assert simulation.calculate(variable, 2031)[0] == 0


def test_dataset_extension_caps_default_and_rejects_explicit_unsupported_end(
    projection, dataset
):
    parameters = CountryTaxBenefitSystem(capital_gains_projection=projection).parameters
    extended = extend_single_year_dataset(dataset, parameters)
    assert extended.years == [2024, 2025, 2026, 2027]
    with pytest.raises(ValueError):
        extend_single_year_dataset(dataset, parameters, end_year=2031)
    dataset.time_period = "2023"
    with pytest.raises(ValueError):
        extend_single_year_dataset(dataset, parameters, end_year=2025)


@pytest.mark.parametrize("before_data_load", [False, True])
def test_rate_reform_shares_projected_inputs_and_applies_response_afterward(
    projection, before_data_load
):
    simulation = Simulation(
        situation={
            "age": {2024: 45},
            "employment_income": {2024: 150_000},
            "capital_gains": {2024: 100_000},
        },
        capital_gains_projection=projection,
        scenario=Scenario(
            applied_before_data_load=before_data_load,
            parameter_changes={
                "gov.hmrc.cgt.higher_rate": {"2026": 0.40},
                "gov.hmrc.cgt.additional_rate": {"2026": 0.40},
                "gov.simulation.capital_gains_responses.elasticity": {"2026": 1.0},
            },
        ),
    )
    before = simulation.calculate("capital_gains_before_response", 2026)[0]
    baseline_before = simulation.baseline.calculate(
        "capital_gains_before_response", 2026
    )[0]
    expected = (
        100_000
        * 1.1
        * 1.2
        / population_factor(simulation.tax_benefit_system.parameters, 2024, 2026)
    )
    assert before == pytest.approx(expected, rel=1e-6)
    assert baseline_before == pytest.approx(expected, rel=1e-6)
    assert simulation.baseline.calculate("capital_gains", 2026)[0] == pytest.approx(
        before
    )
    assert 0 < simulation.calculate("capital_gains", 2026)[0] < before
    assert simulation.calculate("capital_gains_behavioural_response", 2026)[0] < 0


def test_parameter_reset_preserves_projection_without_changing_default_system(
    projection, dataset
):
    simulation = Simulation(
        situation=situation_from(dataset), capital_gains_projection=projection
    )
    simulation.apply_parameter_changes(
        {"gov.hmrc.cgt.annual_exempt_amount": {"2026": 6_000}}
    )
    expected = dataset.person["capital_gains_before_response"] * 1.1 * 1.2
    expected /= population_factor(simulation.tax_benefit_system.parameters, 2024, 2026)
    assert simulation.calculate("capital_gains_before_response", 2026) == pytest.approx(
        expected, rel=1e-6
    )
    default = Simulation(situation=situation_from(dataset))
    index = default.tax_benefit_system.parameters.gov.economic_assumptions.indices.obr.per_capita.gdp
    assert default.calculate("capital_gains_before_response", 2026) == pytest.approx(
        dataset.person["capital_gains_before_response"] * index(2026) / index(2024),
        rel=1e-6,
    )


@pytest.mark.parametrize("reform_type", ["parameter_changes", "reform_dict"])
def test_population_reform_uses_effective_processed_growth(
    projection, dataset, reform_type
):
    changes = {"gov.economic_assumptions.yoy_growth.ons.population": {"2025": 0.02}}
    scenario = (
        Scenario(parameter_changes=changes)
        if reform_type == "parameter_changes"
        else Scenario.from_reform(changes)
    )
    scenario.applied_before_data_load = True
    simulation = Microsimulation(
        dataset=dataset,
        capital_gains_projection=projection,
        scenario=scenario,
    )
    economic = simulation.tax_benefit_system.parameters.gov.economic_assumptions
    assert economic.yoy_growth.ons.population(2025) == pytest.approx(0.02)
    assert economic.yoy_growth.capital_gains(2025) == pytest.approx(1.1 / 1.02 - 1)
    assert simulation.calculate("capital_gains_before_response", 2025).sum() == (
        pytest.approx(150_000 * 1.1, rel=1e-6)
    )
    assert simulation.calculate("capital_gains_before_response", 2025, unweighted=True)[
        0
    ] == pytest.approx(100_000 * 1.1 / 1.02, rel=1e-6)
    baseline_growth = simulation.baseline.tax_benefit_system.parameters.gov.economic_assumptions.yoy_growth.capital_gains
    metadata = economic.yoy_growth.capital_gains.metadata["projection"]
    assert metadata["population_growth"][2025] == pytest.approx(0.02)
    assert (
        metadata["fingerprint"]
        != (baseline_growth.metadata["projection"]["fingerprint"])
    )


@pytest.mark.parametrize("before_data_load", [False, True])
def test_explicit_projection_cannot_disable_economic_assumptions(
    projection, dataset, before_data_load
):
    from policyengine_uk.scenarios.no_economic_assumptions import (
        remove_economic_assumptions,
    )

    with pytest.raises(ValueError):
        Simulation(
            dataset=dataset,
            capital_gains_projection=projection,
            scenario=Scenario(
                simulation_modifier=remove_economic_assumptions,
                applied_before_data_load=before_data_load,
            ),
        )


@pytest.mark.parametrize("reform_type", ["dict", "class"])
def test_default_gains_track_gdp_index_after_late_reform(reform_type):
    from policyengine_core.reforms import Reform

    class ChangeGDPIndex(Reform):
        def apply(self):
            self.parameters.gov.economic_assumptions.indices.obr.per_capita.gdp.update(
                period="2026", value=20
            )

    changes = {"gov.economic_assumptions.indices.obr.per_capita.gdp": {"2026": 20}}
    simulation = Simulation(
        situation={
            "capital_gains": {2024: 100_000},
            "dividend_income": {2024: 100_000},
        },
        reform=changes if reform_type == "dict" else ChangeGDPIndex,
    )
    index = simulation.tax_benefit_system.parameters.gov.economic_assumptions.indices.obr.per_capita.gdp
    assert index(2026) == 20
    expected = 100_000 * 20 / index(2024)
    assert simulation.calculate("capital_gains_before_response", 2026)[
        0
    ] == pytest.approx(expected, rel=1e-6)
    assert simulation.calculate("dividend_income", 2026)[0] == pytest.approx(
        expected, rel=1e-6
    )


def test_remote_dataset_cache_separates_projection_paths(
    projection, dataset, monkeypatch, tmp_path
):
    import policyengine_uk.simulation as simulation_module

    path = tmp_path / "synthetic.h5"
    dataset.save(str(path))
    monkeypatch.setattr(simulation_module, "_url_dataset_cache", {})
    monkeypatch.setattr(
        simulation_module, "download_huggingface_dataset", lambda **kwargs: str(path)
    )
    source = "hf://fixture/synthetic/cgt.h5"
    default = Simulation(dataset=source)
    projected = Simulation(dataset=source, capital_gains_projection=projection)
    different = replace(projection, annual_growth={2025: 0.30, 2026: 0.10, 2027: 0.10})
    alternative = Simulation(dataset=source, capital_gains_projection=different)
    repeated = Simulation(dataset=source, capital_gains_projection=projection)
    expected = (
        100_000
        * 1.1
        * 1.2
        / population_factor(projected.tax_benefit_system.parameters, 2024, 2026)
    )
    assert projected.calculate("capital_gains_before_response", 2026)[
        0
    ] == pytest.approx(expected, rel=1e-6)
    assert repeated.calculate("capital_gains_before_response", 2026)[
        0
    ] == pytest.approx(expected, rel=1e-6)
    assert default.calculate("capital_gains_before_response", 2026)[0] != pytest.approx(
        expected
    )
    assert alternative.calculate("capital_gains_before_response", 2026)[0] != (
        pytest.approx(expected)
    )
