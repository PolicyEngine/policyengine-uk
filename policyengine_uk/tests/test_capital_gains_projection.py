"""Projection mechanics on synthetic records, not estimates for the UK population."""

from dataclasses import FrozenInstanceError, replace
import json

import numpy as np
import pandas as pd
import pytest

from policyengine_uk import CountryTaxBenefitSystem, Microsimulation, Simulation
from policyengine_uk.data.capital_gains_projection import (
    CGT_GROWTH_PATH,
    CGT_INDEX_PATH,
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


@pytest.mark.parametrize(
    "source",
    ["hf://fixture/synthetic/cgt.h5", "gs://fixture/synthetic/cgt.h5@1"],
    ids=["huggingface", "gcs"],
)
def test_remote_dataset_cache_separates_projection_paths(
    projection, dataset, monkeypatch, tmp_path, source
):
    import policyengine_uk.simulation as simulation_module

    path = tmp_path / "synthetic.h5"
    dataset.save(str(path))
    monkeypatch.setattr(simulation_module, "_url_dataset_cache", {})
    monkeypatch.setattr(
        simulation_module, "download_huggingface_dataset", lambda **kwargs: str(path)
    )
    monkeypatch.setattr(
        simulation_module, "materialize_gcs_dataset_url", lambda url: str(path)
    )
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


def generated_parameter_reform(path, kind):
    """Exercise the public reform routes without depending on the guard's class."""
    from policyengine_core.parameters import Parameter
    from policyengine_core.reforms import Reform

    changes = {path: {"2026": 0.10}}

    class UpdateGeneratedParameter(Reform):
        def apply(self):
            self.parameters.get_child(path).update(period="2026", value=0.10)

    class ReplaceGeneratedParameter(Reform):
        def apply(self):
            parent_path, name = path.rsplit(".", 1)
            parent = self.parameters.get_child(parent_path)
            parent.children.pop(name)
            parent.add_child(
                name, Parameter(path, data={"values": {"2026-01-01": 0.10}})
            )

    if kind == "dict":
        return changes
    if kind == "from_dict":
        return Reform.from_dict(changes, country_id="uk")
    if kind == "tuple":
        return ({"gov.hmrc.cgt.annual_exempt_amount": {"2026": 6_000}}, changes)
    if kind == "custom_update":
        return UpdateGeneratedParameter
    if kind == "custom_replacement":
        return ReplaceGeneratedParameter
    raise AssertionError(f"Unknown test reform kind: {kind}")


@pytest.mark.parametrize("path", [CGT_GROWTH_PATH, CGT_INDEX_PATH])
@pytest.mark.parametrize("configured", [False, True], ids=["default", "configured"])
@pytest.mark.parametrize(
    "kind", ["dict", "from_dict", "tuple", "custom_update", "custom_replacement"]
)
def test_generated_parameters_reject_constructor_reforms(
    projection, path, configured, kind
):
    with pytest.raises(ValueError, match="generated.*CapitalGainsProjection"):
        Simulation(
            situation={"capital_gains": {2024: 100_000}},
            capital_gains_projection=projection if configured else None,
            reform=generated_parameter_reform(path, kind),
        )


@pytest.mark.parametrize("path", [CGT_GROWTH_PATH, CGT_INDEX_PATH])
@pytest.mark.parametrize("configured", [False, True], ids=["default", "configured"])
@pytest.mark.parametrize("before_data_load", [False, True])
def test_generated_parameters_reject_scenario_parameter_changes(
    projection, path, configured, before_data_load
):
    with pytest.raises(ValueError, match="generated.*CapitalGainsProjection"):
        Simulation(
            situation={"capital_gains": {2024: 100_000}},
            capital_gains_projection=projection if configured else None,
            scenario=Scenario(
                parameter_changes={path: {"2026": 0.10}},
                applied_before_data_load=before_data_load,
            ),
        )


@pytest.mark.parametrize("path", [CGT_GROWTH_PATH, CGT_INDEX_PATH])
@pytest.mark.parametrize("configured", [False, True], ids=["default", "configured"])
@pytest.mark.parametrize(
    "route",
    [
        "dict",
        "custom_update",
        "custom_replacement",
        "parameter_changes",
        "scenario_apply",
    ],
)
def test_generated_parameters_reject_runtime_changes(
    projection, path, configured, route
):
    simulation = Simulation(
        situation={"capital_gains": {2024: 100_000}},
        capital_gains_projection=projection if configured else None,
    )
    with pytest.raises(ValueError, match="generated.*CapitalGainsProjection"):
        if route == "parameter_changes":
            simulation.apply_parameter_changes({path: {"2026": 0.10}})
        elif route == "scenario_apply":
            # On an already-built simulation, parameter_changes accepts a
            # scalar or nested parameter children, rather than year-keyed values.
            Scenario(parameter_changes={path: 0.10}).apply(simulation)
        else:
            simulation.apply_reform(generated_parameter_reform(path, route))


@pytest.mark.parametrize("path", [CGT_GROWTH_PATH, CGT_INDEX_PATH])
@pytest.mark.parametrize("configured", [False, True], ids=["default", "configured"])
def test_generated_parameters_reject_runtime_scenario_modifier_replacement(
    projection, path, configured
):
    from policyengine_core.parameters import Parameter

    simulation = Simulation(
        situation={"capital_gains": {2024: 100_000}},
        capital_gains_projection=projection if configured else None,
    )

    def replace_generated(simulation):
        parent_path, name = path.rsplit(".", 1)
        parent = simulation.tax_benefit_system.parameters.get_child(parent_path)
        parent.children.pop(name)
        parent.add_child(name, Parameter(path, data={"values": {"2026-01-01": 0.50}}))

    with pytest.raises(ValueError, match="generated.*CapitalGainsProjection"):
        Scenario(simulation_modifier=replace_generated).apply(simulation)


def test_runtime_scenario_modifier_supports_simulations_without_projection_hook():
    from types import SimpleNamespace

    simulation = SimpleNamespace(modified=False)

    def modifier(simulation):
        simulation.modified = True

    Scenario(simulation_modifier=modifier).apply(simulation)
    assert simulation.modified
    assert not hasattr(simulation, "_scenario_apply_to_built_simulation")


def test_dated_reform_cache_does_not_share_projection_configuration(projection):
    """The same dated tax reform must retain each caller's gains assumptions."""
    changes = {"gov.hmrc.cgt.annual_exempt_amount": {"2026": 6_123}}
    simulations = [
        Simulation(
            situation={"capital_gains": {2024: 100_000}},
            capital_gains_projection=configuration,
            reform=changes,
        )
        for configuration in (None, projection, None)
    ]
    default, configured, default_again = simulations
    index = default.tax_benefit_system.parameters.gov.economic_assumptions.indices.obr.per_capita.gdp
    default_expected = 100_000 * index(2026) / index(2024)
    configured_expected = (
        100_000
        * aggregate_factor(projection, 2026)
        / population_factor(configured.tax_benefit_system.parameters, 2024, 2026)
    )
    for simulation, expected in (
        (default, default_expected),
        (configured, configured_expected),
        (default_again, default_expected),
    ):
        assert (
            simulation.tax_benefit_system.parameters.gov.hmrc.cgt.annual_exempt_amount(
                2026
            )
            == pytest.approx(6_123)
        )
        assert simulation.calculate("capital_gains_before_response", 2026)[
            0
        ] == pytest.approx(expected, rel=1e-6)
        assert simulation.baseline.calculate("capital_gains_before_response", 2026)[
            0
        ] == pytest.approx(expected, rel=1e-6)
    assert configured.capital_gains_projection_metadata[
        "configuration_fingerprint"
    ] == (projection.fingerprint)
    assert (
        default_again.capital_gains_projection_metadata["name"]
        == (default.capital_gains_projection_metadata["name"])
    )
    assert default_expected != pytest.approx(configured_expected)


def test_shared_horizon_extension_preserves_finite_cgt_boundary(dataset, monkeypatch):
    from policyengine_uk.data import economic_assumptions

    # Model #2376's integration without importing its unmerged horizon change.
    monkeypatch.setattr(economic_assumptions, "PROJECTION_END_YEAR", 2032)
    default = Simulation(dataset=dataset)
    finite = Simulation(dataset=dataset, capital_gains_projection=obr_eot_projection())
    assert default.dataset.years == list(range(2024, 2033))
    assert finite.dataset.years == list(range(2024, 2031))
    with pytest.raises(ValueError, match="supports.*2030"):
        extend_single_year_dataset(
            dataset, finite.tax_benefit_system.parameters, end_year=2032
        )
    with pytest.raises(ValueError, match="supports.*2030"):
        finite.calculate("capital_gains_before_response", 2031)


def test_supplied_gains_report_unused_projection_without_changing_values(dataset):
    """A selected scenario must not claim credit for GDP-preprojected inputs."""
    import warnings

    materialized = extend_single_year_dataset(
        dataset, CountryTaxBenefitSystem().parameters, end_year=2030
    )
    original = Simulation(dataset=materialized)
    expected = {
        variable: original.calculate(variable, 2026).copy() for variable in INPUTS
    }
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        simulation = Simulation(
            dataset=materialized, capital_gains_projection=obr_eot_projection()
        )
        # Inspecting configuration is not an attempt to project a requested year.
        initial_metadata = simulation.capital_gains_projection_metadata
        assert not caught
        for variable in INPUTS:
            np.testing.assert_array_equal(
                simulation.calculate(variable, 2026), expected[variable]
            )
        first_warning_count = len(caught)
        simulation.calculate("capital_gains_before_response", 2026)
        assert len(caught) == first_warning_count

    application = initial_metadata["application"]
    assert initial_metadata["configuration_scope"] == "configured_assumptions"
    for variable in INPUTS:
        record = application["by_variable"][variable]["2026"]
        assert record["status"] == "supplied"
        assert record["projection_fingerprint"] is None
    assert application["by_period"]["2026"]["status"] == "supplied"
    assert set(application["by_period"]["2026"]["covered_variables"]) == set(INPUTS)
    unused = [
        warning
        for warning in caught
        if warning.category.__name__ == "UnusedCapitalGainsProjectionWarning"
    ]
    assert len(unused) == 1
    assert "supplied" in str(unused[0].message).lower()


def test_single_year_extension_records_applied_projection(dataset, projection):
    simulation = Simulation(dataset=dataset, capital_gains_projection=projection)
    metadata = simulation.capital_gains_projection_metadata
    records = metadata["application"]["by_variable"]
    for variable in INPUTS:
        assert records[variable]["2024"]["status"] == "supplied"
        for year in (2025, 2026, 2027):
            record = records[variable][str(year)]
            assert record["status"] == "projected"
            assert record["method"] == "dataset_extension"
            assert record["source_period"] is not None
            assert record["projection_fingerprint"] == metadata["fingerprint"]
            expected = dataset.person[variable] * aggregate_factor(projection, year)
            expected /= population_factor(
                simulation.tax_benefit_system.parameters, 2024, year
            )
            assert simulation.calculate(variable, year) == pytest.approx(
                expected, rel=1e-6
            )
    assert metadata["application"]["by_period"]["2026"]["status"] == "projected"
    # Returning provenance does not expose the simulation's mutable records.
    records[INPUTS[0]]["2026"]["status"] = "corrupted"
    assert (
        simulation.capital_gains_projection_metadata["application"]["by_variable"][
            INPUTS[0]
        ]["2026"]["status"]
        == "projected"
    )


def test_household_projection_records_mixed_components_and_periods(projection):
    import warnings

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        simulation = Simulation(
            situation={
                "capital_gains": {2024: 100_000, 2026: 0},
                "capital_gains_badr": {2024: 10_000},
            },
            capital_gains_projection=projection,
        )
        simulation.capital_gains_projection_metadata
        assert not caught
        # Calculate a projected component before the explicit zero so the
        # completed calculations demonstrate mixed application in the year.
        assert simulation.calculate("capital_gains_badr", 2026)[0] > 10_000
        assert simulation.calculate("capital_gains_before_response", 2026)[0] == 0
        assert simulation.calculate("capital_gains_residential_property", 2026)[0] == 0
        assert simulation.calculate("capital_gains_before_response", 2025)[0] > 100_000

    application = simulation.capital_gains_projection_metadata["application"]
    records = application["by_variable"]
    assert records["capital_gains_before_response"]["2026"]["status"] == "supplied"
    for variable, year in (
        ("capital_gains_before_response", "2025"),
        ("capital_gains_badr", "2026"),
    ):
        assert records[variable][year]["status"] == "projected"
        assert records[variable][year]["method"] == "input_uprating"
        assert records[variable][year]["source_period"] == "2024"
    assert records["capital_gains_residential_property"]["2026"]["status"] == "default"
    assert application["by_period"]["2026"]["status"] == "mixed"
    assert not [
        warning
        for warning in caught
        if warning.category.__name__ == "UnusedCapitalGainsProjectionWarning"
    ]


def test_absent_gains_do_not_claim_projection_or_warn(projection):
    import warnings

    simulation = Simulation(situation={"age": 45}, capital_gains_projection=projection)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        for variable in INPUTS:
            assert simulation.calculate(variable, 2031)[0] == 0
    records = simulation.capital_gains_projection_metadata["application"]["by_variable"]
    for variable in INPUTS:
        record = records[variable]["2031"]
        assert record["status"] == "default"
        assert record["projection_fingerprint"] is None
    assert not [
        warning
        for warning in caught
        if warning.category.__name__ == "UnusedCapitalGainsProjectionWarning"
    ]


def test_projection_provenance_survives_cache_and_input_replacement(projection):
    import warnings

    simulation = Simulation(
        situation={"capital_gains": {2024: 100_000}},
        capital_gains_projection=projection,
    )
    first = simulation.calculate("capital_gains_before_response", 2026).copy()
    first_record = simulation.capital_gains_projection_metadata["application"][
        "by_variable"
    ]["capital_gains_before_response"]["2026"]
    np.testing.assert_array_equal(
        simulation.calculate("capital_gains_before_response", 2026), first
    )
    assert (
        simulation.capital_gains_projection_metadata["application"]["by_variable"][
            "capital_gains_before_response"
        ]["2026"]
        == first_record
    )
    assert first_record["status"] == "projected"

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        simulation.set_input("capital_gains_before_response", 2026, [0])
        assert simulation.calculate("capital_gains_before_response", 2026)[0] == 0
    replacement = simulation.capital_gains_projection_metadata["application"][
        "by_variable"
    ]["capital_gains_before_response"]["2026"]
    assert replacement["status"] == "supplied"
    assert replacement["projection_fingerprint"] is None
    simulation.delete_arrays("capital_gains_before_response", 2026)
    np.testing.assert_array_equal(
        simulation.calculate("capital_gains_before_response", 2026), first
    )
    assert (
        simulation.capital_gains_projection_metadata["application"]["by_variable"][
            "capital_gains_before_response"
        ]["2026"]["status"]
        == "projected"
    )


def test_projection_application_records_are_independent_of_baseline(projection):
    simulation = Simulation(
        situation={"capital_gains": {2024: 100_000}},
        capital_gains_projection=projection,
        reform={"gov.hmrc.cgt.higher_rate": {"2026": 0.4}},
    )
    baseline_before = simulation.baseline.capital_gains_projection_metadata
    expected = simulation.calculate("capital_gains_before_response", 2026)
    assert simulation.baseline.capital_gains_projection_metadata == baseline_before
    actual = simulation.baseline.calculate("capital_gains_before_response", 2026)
    np.testing.assert_array_equal(actual, expected)
    assert (
        simulation.capital_gains_projection_metadata["application"]
        == (simulation.baseline.capital_gains_projection_metadata["application"])
    )
    clone = simulation.clone()
    clone.calculate("capital_gains_before_response", 2027)
    original_records = simulation.capital_gains_projection_metadata["application"][
        "by_variable"
    ]["capital_gains_before_response"]
    assert "2027" not in original_records


def test_cached_dataset_extension_retains_application_provenance(
    dataset, projection, monkeypatch, tmp_path
):
    import policyengine_uk.simulation as simulation_module

    path = tmp_path / "synthetic.h5"
    dataset.save(str(path))
    monkeypatch.setattr(simulation_module, "_url_dataset_cache", {})
    downloads = []

    def download(**kwargs):
        downloads.append(kwargs)
        return str(path)

    monkeypatch.setattr(simulation_module, "download_huggingface_dataset", download)
    source = "hf://synthetic/uk/synthetic.h5"
    first = Simulation(dataset=source, capital_gains_projection=projection)
    second = Simulation(dataset=source, capital_gains_projection=projection)
    assert len(downloads) == 1
    for simulation in (first, second):
        metadata = simulation.capital_gains_projection_metadata
        record = metadata["application"]["by_variable"][
            "capital_gains_before_response"
        ]["2026"]
        assert record["status"] == "projected"
        assert record["method"] == "dataset_extension"
        assert record["projection_fingerprint"] == metadata["fingerprint"]
    np.testing.assert_array_equal(
        first.calculate("capital_gains_before_response", 2026),
        second.calculate("capital_gains_before_response", 2026),
    )


@pytest.mark.parametrize("data_source", ["household", "dataset"])
def test_runtime_population_reform_reports_fingerprint_actually_applied(
    projection, dataset, data_source
):
    kwargs = (
        {"situation": situation_from(dataset)}
        if data_source == "household"
        else {"dataset": dataset}
    )
    simulation = Simulation(capital_gains_projection=projection, **kwargs)
    before = simulation.calculate("capital_gains_before_response", 2026).copy()
    old_fingerprint = simulation.capital_gains_projection_metadata["fingerprint"]
    simulation.apply_reform(
        {"gov.economic_assumptions.yoy_growth.ons.population": {"2026": 0.05}}
    )
    after = simulation.calculate("capital_gains_before_response", 2026)
    metadata = simulation.capital_gains_projection_metadata
    record = metadata["application"]["by_variable"]["capital_gains_before_response"][
        "2026"
    ]
    assert metadata["fingerprint"] != old_fingerprint
    if data_source == "household":
        expected = dataset.person["capital_gains_before_response"]
        expected = (
            expected
            * aggregate_factor(projection, 2026)
            / population_factor(simulation.tax_benefit_system.parameters, 2024, 2026)
        )
        assert after == pytest.approx(expected, rel=1e-6)
        assert after[0] != pytest.approx(before[0])
        assert record["projection_fingerprint"] == metadata["fingerprint"]
    else:
        np.testing.assert_array_equal(after, before)
        assert record["projection_fingerprint"] == old_fingerprint
    assert record["status"] == "projected"


def test_default_component_does_not_warn_about_other_supplied_gains(projection):
    import warnings

    simulation = Simulation(
        situation={"capital_gains": {2024: 100_000, 2026: 120_000}},
        capital_gains_projection=projection,
    )
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        assert simulation.calculate("capital_gains_residential_property", 2026)[0] == 0
    assert not [
        warning
        for warning in caught
        if warning.category.__name__ == "UnusedCapitalGainsProjectionWarning"
    ]
    with pytest.warns(UserWarning, match="supplied"):
        assert simulation.calculate("capital_gains_before_response", 2026)[0] == 120_000


def test_frozen_dataset_does_not_retain_extension_application_claim(
    dataset, projection
):
    from policyengine_uk.scenarios import no_economic_assumptions

    projected = Simulation(dataset=dataset, capital_gains_projection=projection)
    frozen = Simulation(dataset=projected.dataset, scenario=no_economic_assumptions)
    for variable in INPUTS:
        assert frozen.calculate(variable, 2026) == pytest.approx(
            dataset.person[variable], rel=1e-6
        )
        record = frozen.capital_gains_projection_metadata["application"]["by_variable"][
            variable
        ]["2026"]
        assert record["status"] == "unknown"
        assert record["projection_fingerprint"] is None
    # Freezing a copy must not change the original simulation's receipt.
    original = projected.capital_gains_projection_metadata
    assert (
        original["application"]["by_variable"]["capital_gains_before_response"]["2026"][
            "projection_fingerprint"
        ]
        == original["fingerprint"]
    )


@pytest.mark.parametrize("route", ["neutralize_variable", "synthetic_abolition"])
def test_neutralized_supplied_gains_report_default_without_unused_warning(
    projection, route
):
    import warnings

    from policyengine_core.parameters import Parameter, ParameterNode
    from policyengine_core.reforms import Reform
    from policyengine_uk.variables.gov.hmrc.capital_gains_tax.capital_gains_before_response import (
        capital_gains_before_response,
    )

    class NeutralizeGains(Reform):
        def apply(self):
            if route == "neutralize_variable":
                self.neutralize_variable("capital_gains_before_response")
            else:
                # Core omits input variables from its generated abolition flags.
                # Add one explicitly to exercise its parameter-based default route.
                if "abolitions" not in self.parameters.gov.children:
                    self.parameters.gov.add_child(
                        "abolitions", ParameterNode("gov.abolitions", data={})
                    )
                self.parameters.gov.abolitions.add_child(
                    "capital_gains_before_response",
                    Parameter(
                        "gov.abolitions.capital_gains_before_response",
                        data={"values": {"2026-01-01": True}},
                    ),
                )

    class RestoreGains(Reform):
        def apply(self):
            self.replace_variable(capital_gains_before_response)

    simulation = Simulation(
        situation={"capital_gains": {2024: 100_000, 2026: 120_000}},
        capital_gains_projection=projection,
    )
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        simulation.apply_reform(NeutralizeGains)
        assert simulation.calculate("capital_gains_before_response", 2026)[0] == 0
        record = simulation.capital_gains_projection_metadata["application"][
            "by_variable"
        ]["capital_gains_before_response"]["2026"]
        simulation.delete_arrays("capital_gains_before_response", 2030)
        after_delete = simulation.capital_gains_projection_metadata["application"][
            "by_variable"
        ]["capital_gains_before_response"]["2026"]
        assert after_delete == record
        simulation.set_input("capital_gains_before_response", 2026, [555])
        after_replacement = simulation.capital_gains_projection_metadata["application"][
            "by_variable"
        ]["capital_gains_before_response"]["2026"]
        assert after_replacement == record
        assert simulation.calculate("capital_gains_before_response", 2026)[0] == 0
    assert record["status"] == "default"
    assert record["method"] == "default"
    assert record["projection_fingerprint"] is None
    assert not [
        warning
        for warning in caught
        if warning.category.__name__ == "UnusedCapitalGainsProjectionWarning"
    ]
    if route == "neutralize_variable":
        simulation.apply_reform(RestoreGains)
    else:
        simulation.apply_reform(
            {"gov.abolitions.capital_gains_before_response": {"2026": False}}
        )
    with pytest.warns(UserWarning, match="supplied"):
        assert simulation.calculate("capital_gains_before_response", 2026)[0] == 555
    restored_record = simulation.capital_gains_projection_metadata["application"][
        "by_variable"
    ]["capital_gains_before_response"]["2026"]
    assert restored_record["status"] == "supplied"
    assert restored_record["projection_fingerprint"] is None


def test_restoring_neutralized_projection_preserves_applied_fingerprint(
    dataset, projection
):
    from policyengine_core.reforms import Reform
    from policyengine_uk.variables.gov.hmrc.capital_gains_tax.capital_gains_before_response import (
        capital_gains_before_response,
    )

    class NeutralizeGains(Reform):
        def apply(self):
            self.neutralize_variable("capital_gains_before_response")

    class RestoreGains(Reform):
        def apply(self):
            self.replace_variable(capital_gains_before_response)

    simulation = Simulation(dataset=dataset, capital_gains_projection=projection)
    original = simulation.calculate("capital_gains_before_response", 2026).copy()
    original_record = simulation.capital_gains_projection_metadata["application"][
        "by_variable"
    ]["capital_gains_before_response"]["2026"]
    simulation.apply_reform(NeutralizeGains)
    np.testing.assert_array_equal(
        simulation.calculate("capital_gains_before_response", 2026), np.zeros(3)
    )
    neutralized_record = simulation.capital_gains_projection_metadata["application"][
        "by_variable"
    ]["capital_gains_before_response"]["2026"]
    assert neutralized_record["status"] == "default"
    assert neutralized_record["projection_fingerprint"] is None
    simulation.delete_arrays("capital_gains_before_response", 2030)
    assert (
        simulation.capital_gains_projection_metadata["application"]["by_variable"][
            "capital_gains_before_response"
        ]["2026"]
        == neutralized_record
    )
    simulation.apply_reform(RestoreGains)
    np.testing.assert_array_equal(
        simulation.calculate("capital_gains_before_response", 2026), original
    )
    restored_record = simulation.capital_gains_projection_metadata["application"][
        "by_variable"
    ]["capital_gains_before_response"]["2026"]
    assert restored_record == original_record


def test_failed_population_override_preserves_generated_projection_and_recovers():
    from policyengine_uk.utils.dated_reforms import LegacyOverride

    population_path = "gov.economic_assumptions.yoy_growth.ons.population"
    projection = obr_eot_projection()
    simulation = Simulation(
        situation={"capital_gains": {2024: 100_000}},
        capital_gains_projection=projection,
    )
    original_values = simulation.calculate("capital_gains_before_response", 2026).copy()
    original_metadata = simulation.capital_gains_projection_metadata
    system = simulation.tax_benefit_system
    original_population = system.parameters.get_child(population_path)(2026)
    original_nodes = {
        path: system.parameters.get_child(path)
        for path in (CGT_GROWTH_PATH, CGT_INDEX_PATH)
    }
    original_factors = {path: node(2026) for path, node in original_nodes.items()}

    with pytest.raises(ValueError, match="population"):
        system.add_legacy_overrides([LegacyOverride(population_path, "2026", -1)])
    assert system.legacy_overrides == []
    assert system.parameters.get_child(population_path)(2026) == original_population
    for path, node in original_nodes.items():
        assert system.parameters.get_child(path) is node
        assert node(2026) == original_factors[path]
    assert simulation.capital_gains_projection_metadata == original_metadata
    simulation.delete_arrays("capital_gains_before_response", 2026)
    np.testing.assert_array_equal(
        simulation.calculate("capital_gains_before_response", 2026), original_values
    )

    simulation.apply_reform({population_path: {"2026": 0.05}})
    expected = (
        100_000
        * aggregate_factor(projection, 2026)
        / population_factor(system.parameters, 2024, 2026)
    )
    after = simulation.calculate("capital_gains_before_response", 2026)
    assert after[0] == pytest.approx(expected, rel=1e-6)
    assert after[0] != pytest.approx(original_values[0])
    assert (
        simulation.capital_gains_projection_metadata["fingerprint"]
        != (original_metadata["fingerprint"])
    )
