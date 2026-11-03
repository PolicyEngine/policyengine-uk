"""Dataset energy prices move only when their price basis is declared.

The controlled index levels are test data for the annual projection contract,
not forecasts: every calendar and fiscal year energy price index is set to the
same levels, so the expected amounts are simple ratios.
"""

import json

import h5py
import numpy as np
import pandas as pd
import pytest
from policyengine_core.data import Dataset

import policyengine_uk.simulation as simulation_module
from policyengine_uk import CountryTaxBenefitSystem, Simulation
from policyengine_uk.data import UKMultiYearDataset, UKSingleYearDataset
from policyengine_uk.data.economic_assumptions import (
    apply_uprating,
    extend_single_year_dataset,
    reset_growthfactor_uprating,
    uprating_input_fingerprint,
    uprating_input_paths,
)
from policyengine_uk.scenarios import no_economic_assumptions
from policyengine_uk.utils.scenario import Scenario

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

ENERGY = (
    "domestic_energy_consumption",
    "electricity_consumption",
    "gas_consumption",
)
ENERGY_PRICES = "gov.economic_assumptions.energy_prices"
INDICES = tuple(
    f"{ENERGY_PRICES}.{kind}.{series}"
    for kind in ("calendar_year", "fiscal_year")
    for series in ("electricity", "gas", "electricity_gas_and_solid_fuels")
)
LEVELS = dict(enumerate([100, 110, 125, 150, 160, 170, 180, 190, 200], 2024))
DECLARATION = {"period_type": "calendar_year", "period_value": 2024}


def energy_dataset(basis=None, year=2024):
    return UKSingleYearDataset(
        person=pd.DataFrame(
            {
                "person_id": [1, 2],
                "person_benunit_id": [1, 2],
                "person_household_id": [1, 2],
                "age": [40, 50],
            }
        ),
        benunit=pd.DataFrame({"benunit_id": [1, 2]}),
        household=pd.DataFrame(
            {
                "household_id": [1, 2],
                "region": ["LONDON", "WALES"],
                "tenure_type": ["OWNED_OUTRIGHT", "OWNED_OUTRIGHT"],
                "council_tax": [0.0, 0.0],
                "rent": [0.0, 0.0],
                "household_weight": [1.0, 2.0],
                **dict.fromkeys(ENERGY, [100.0, 0.0]),
            }
        ),
        fiscal_year=year,
        energy_price_basis=basis,
    )


@pytest.fixture
def parameters():
    parameters = CountryTaxBenefitSystem().parameters.clone()
    # In particular, 2026 / 2024 = 125 / 100 and 2027 / 2026 = 150 / 125.
    for path in INDICES:
        index = parameters.get_child(path)
        for year, value in LEVELS.items():
            index.update(period=str(year), value=value)
    return parameters


def energy_file(tmp_path, declaration=None):
    path = tmp_path / "renamed-input.h5"
    energy_dataset().save(path)
    if declaration is not None:
        with h5py.File(path, "a") as file:
            file.attrs["energy_price_basis"] = json.dumps(declaration)
    return path


@pytest.mark.parametrize("period_type", ["calendar_year", "fiscal_year"])
def test_declared_2024_prices_reach_2026_without_changing_the_source(
    tmp_path, parameters, period_type
):
    declaration = {"period_type": period_type, "period_value": 2024}
    source = UKSingleYearDataset(file_path=energy_file(tmp_path, declaration))
    projected = extend_single_year_dataset(source, parameters, end_year=2026)
    for variable in ENERGY:
        np.testing.assert_allclose(projected[2026].household[variable], [125.0, 0.0])
        np.testing.assert_array_equal(source.household[variable], [100.0, 0.0])
    assert source.energy_price_basis == declaration


def test_unlabelled_energy_stays_flat_through_the_dataset_horizon(parameters):
    source = energy_dataset()
    projected = extend_single_year_dataset(source, parameters, end_year=2032)
    for year in [2026, 2027, 2031, 2032]:
        for variable in ENERGY:
            np.testing.assert_array_equal(projected[year].household[variable], [100, 0])


def test_2026_price_basis_is_identity_in_2026_and_grows_afterwards(
    tmp_path, parameters
):
    source = UKSingleYearDataset(
        file_path=energy_file(
            tmp_path, {"period_type": "fiscal_year", "period_value": 2026}
        )
    )
    projected = extend_single_year_dataset(source, parameters, end_year=2027)
    for variable in ENERGY:
        np.testing.assert_array_equal(projected[2026].household[variable], [100, 0])
        np.testing.assert_allclose(projected[2027].household[variable], [120, 0])


@pytest.mark.parametrize("missing", [ENERGY[:1], ENERGY[1:], ENERGY])
def test_partial_or_absent_energy_columns_do_not_create_inputs(parameters, missing):
    source = energy_dataset(DECLARATION)
    source.household = source.household.drop(columns=list(missing))
    unlabelled = source.copy()
    unlabelled.energy_price_basis = None
    control = extend_single_year_dataset(unlabelled, parameters, end_year=2032)
    projected = extend_single_year_dataset(source, parameters, end_year=2032)
    for year in (2026, 2032):
        assert not set(missing) & set(projected[year].household.columns)
        for variable in set(ENERGY) - set(missing):
            np.testing.assert_allclose(
                projected[year].household[variable], [LEVELS[year], 0]
            )
        np.testing.assert_array_equal(
            projected[year].household.household_weight,
            control[year].household.household_weight,
        )


def test_energy_declaration_does_not_change_other_consumption_uprating(parameters):
    food = "food_and_non_alcoholic_beverages_consumption"
    growth = parameters.get_child(
        "gov.economic_assumptions.yoy_growth.obr.consumer_price_index"
    )
    growth.update(period="2025", value=0.1)
    growth.update(period="2026", value=0.2)
    unlabelled = energy_dataset()
    unlabelled.household[food] = [50.0, 0.0]
    labelled = unlabelled.copy()
    labelled.energy_price_basis = DECLARATION
    plain = extend_single_year_dataset(unlabelled, parameters, end_year=2026)
    declared = extend_single_year_dataset(labelled, parameters, end_year=2026)
    for projected in (plain, declared):
        np.testing.assert_allclose(projected[2026].household[food], [66.0, 0.0])
    for variable in ENERGY:
        np.testing.assert_allclose(plain[2026].household[variable], [100.0, 0.0])
        np.testing.assert_allclose(declared[2026].household[variable], [125.0, 0.0])


def test_reapplying_uprating_recomputes_from_the_original_observation(parameters):
    source = energy_dataset(DECLARATION)
    once = extend_single_year_dataset(source, parameters, end_year=2032)
    twice = apply_uprating(once, parameters)
    for year in once.years:
        for variable in ENERGY:
            np.testing.assert_array_equal(
                twice[year].household[variable], once[year].household[variable]
            )
        assert twice[year].energy_price_basis == once[year].energy_price_basis
    assert source.energy_price_basis == DECLARATION
    assert once[2026].energy_price_basis == {
        "period_type": "fiscal_year",
        "period_value": 2026,
    }


def test_serialized_projected_child_extends_without_double_projection(
    tmp_path, parameters
):
    source = energy_dataset(DECLARATION)
    one_shot = extend_single_year_dataset(source, parameters, end_year=2027)
    child = one_shot[2026].copy()
    path = tmp_path / "child-with-an-unrelated-filename.h5"
    child.save(path)
    loaded = UKSingleYearDataset(file_path=path)
    assert loaded.energy_price_basis == {
        "period_type": "fiscal_year",
        "period_value": 2026,
    }
    extended = extend_single_year_dataset(loaded, parameters, end_year=2027)
    for variable in ENERGY:
        np.testing.assert_allclose(extended[2027].household[variable], [150.0, 0.0])
        np.testing.assert_allclose(
            extended[2027].household[variable], one_shot[2027].household[variable]
        )
        np.testing.assert_array_equal(source.household[variable], [100.0, 0.0])
    assert source.energy_price_basis == DECLARATION


def test_reset_restores_original_amounts_and_original_kind(parameters):
    projected = extend_single_year_dataset(
        energy_dataset(DECLARATION), parameters, end_year=2027
    )
    frozen = reset_growthfactor_uprating(projected.copy())
    for year in frozen.years:
        assert frozen[year].energy_price_basis == DECLARATION
        for variable in ENERGY:
            np.testing.assert_array_equal(frozen[year].household[variable], [100, 0])
    for variable in ENERGY:
        np.testing.assert_allclose(projected[2027].household[variable], [150, 0])


def controlled_changes(target=125):
    return {
        path: {
            f"year:{year}-01-01:1": target if year == 2026 else value
            for year, value in LEVELS.items()
        }
        for path in INDICES
    }


def before_load(target=125):
    return Scenario(
        parameter_changes=controlled_changes(target), applied_before_data_load=True
    )


def assert_energy(simulation, year, expected):
    for variable in ENERGY:
        np.testing.assert_allclose(simulation.calculate(variable, year), [expected, 0])


def core_arrays(source):
    system = CountryTaxBenefitSystem()
    arrays = {}
    for table in source.tables:
        for variable in table.columns:
            values = table[variable].to_numpy()
            possible_values = getattr(
                system.variables[variable], "possible_values", None
            )
            if possible_values is not None:
                values = np.asarray(possible_values.encode(values))
            arrays[variable] = {source.time_period: values}
    return arrays


class InMemoryCore(Dataset):
    """Synthetic Core input with the public load_dataset interface, no file."""

    def __init__(self, arrays):
        self.arrays = arrays

    def load_dataset(self):
        return self.arrays


def core_file(source, path, basis=None):
    with h5py.File(path, "w") as file:
        for variable, periods in core_arrays(source).items():
            for period, values in periods.items():
                file.create_dataset(f"{variable}/{period}", data=values)
        if basis is not None:
            file.attrs["energy_price_basis"] = json.dumps(basis)
    return path


@pytest.mark.parametrize(
    "source_kind", ["single", "uk_h5", "core_h5", "core_instance", "core_class"]
)
def test_declared_inputs_reach_the_same_projection(source_kind, tmp_path, monkeypatch):
    original = energy_dataset(DECLARATION)
    source = original
    if source_kind == "uk_h5":
        source = tmp_path / "producer-2026-does-not-define-price-year.h5"
        original.save(source)
    elif source_kind == "core_h5":
        source = core_file(original, tmp_path / "renamed-core.h5", DECLARATION)
    elif source_kind in ("core_instance", "core_class"):
        source = InMemoryCore(core_arrays(original))
        if source_kind == "core_instance":
            source.energy_price_basis = dict(DECLARATION)
        else:
            monkeypatch.setattr(
                InMemoryCore, "energy_price_basis", dict(DECLARATION), raising=False
            )
    simulation = Simulation(dataset=source, scenario=before_load())
    assert_energy(simulation, 2026, 125)
    assert original.energy_price_basis == DECLARATION
    for variable in ENERGY:
        np.testing.assert_array_equal(original.household[variable], [100, 0])


def test_unlabelled_in_memory_core_input_stays_flat():
    source = InMemoryCore(core_arrays(energy_dataset()))
    simulation = Simulation(dataset=source, scenario=before_load())
    for year in (2026, 2027, 2032):
        assert_energy(simulation, year, 100)


def test_core_file_and_explicit_field_must_agree(tmp_path):
    path = core_file(energy_dataset(), tmp_path / "core.h5", DECLARATION)
    source = Dataset.from_file(path)
    source.energy_price_basis = {"period_type": "fiscal_year", "period_value": 2024}
    with pytest.raises(ValueError, match="energy_price_basis"):
        Simulation(dataset=source)


@pytest.fixture
def remote_energy(monkeypatch, tmp_path):
    path = tmp_path / "arbitrary-price-basis.h5"
    energy_dataset(DECLARATION).save(path)
    monkeypatch.setattr(simulation_module, "_url_dataset_cache", {})
    monkeypatch.setattr(
        simulation_module, "download_huggingface_dataset", lambda **_: str(path)
    )
    monkeypatch.setattr(
        simulation_module, "materialize_gcs_dataset_url", lambda url: str(path)
    )
    return path


@pytest.mark.parametrize(
    "url", ["hf://policyengine/mock/prices.h5", "gs://mock/prices.h5"]
)
@pytest.mark.parametrize("reformed_first", [False, True])
def test_remote_projection_and_baseline_are_isolated_in_both_orders(
    remote_energy, url, reformed_first
):
    if reformed_first:
        reformed = Simulation(dataset=url, reform=controlled_changes(160))
        current = Simulation(dataset=url)
    else:
        current = Simulation(dataset=url)
        reformed = Simulation(dataset=url, reform=controlled_changes(160))
    assert_energy(reformed, 2026, 160)
    for variable in ENERGY:
        np.testing.assert_array_equal(
            current.calculate(variable, 2026),
            reformed.baseline.calculate(variable, 2026),
        )
    repeated = Simulation(dataset=url)
    for variable in ENERGY:
        np.testing.assert_array_equal(
            repeated.calculate(variable, 2026), current.calculate(variable, 2026)
        )


def test_index_only_reform_dict_matches_before_load_scenario():
    source = energy_dataset(DECLARATION)
    by_dict = Simulation(dataset=source, reform=controlled_changes(160))
    by_scenario = Simulation(dataset=source, scenario=before_load(160))
    assert_energy(by_dict, 2026, 160)
    for year in (2024, 2025, 2026, 2027, 2032):
        for variable in ENERGY:
            np.testing.assert_array_equal(
                by_dict.calculate(variable, year), by_scenario.calculate(variable, year)
            )


@pytest.mark.parametrize("path", INDICES)
def test_energy_price_index_changes_the_projection_fingerprint(parameters, path):
    assert any(path.startswith(f"{read}.") for read in uprating_input_paths())
    changed = parameters.clone()
    changed.get_child(path).update(period="2026", value=160)
    assert uprating_input_fingerprint(parameters) != uprating_input_fingerprint(changed)
    assert uprating_input_fingerprint(parameters) == uprating_input_fingerprint(
        parameters.clone()
    )


@pytest.mark.parametrize("frozen_first", [False, True])
def test_no_economic_assumptions_does_not_contaminate_cached_energy(
    remote_energy, frozen_first
):
    url = "hf://policyengine/mock/prices.h5"
    if frozen_first:
        frozen = Simulation(dataset=url, scenario=no_economic_assumptions)
        current = Simulation(dataset=url)
    else:
        current = Simulation(dataset=url)
        frozen = Simulation(dataset=url, scenario=no_economic_assumptions)
    for year in (2026, 2027, 2032):
        assert_energy(frozen, year, 100)
        assert frozen.dataset[year].energy_price_basis == DECLARATION
    repeated = Simulation(dataset=url)
    for variable in ENERGY:
        np.testing.assert_array_equal(
            repeated.calculate(variable, 2026), current.calculate(variable, 2026)
        )


@pytest.mark.parametrize("source_kind", ["single", "local", "core", "gcs"])
def test_no_economic_reset_keeps_loaded_amounts_and_metadata_coherent(
    remote_energy, source_kind
):
    original = energy_dataset(DECLARATION)
    if source_kind == "single":
        source = original
    elif source_kind == "local":
        source = remote_energy
    elif source_kind == "core":
        source = InMemoryCore(core_arrays(original))
        source.energy_price_basis = dict(DECLARATION)
    else:
        source = "gs://mock/prices.h5"
    frozen = Simulation(dataset=source, scenario=no_economic_assumptions)
    for year in (2024, 2026, 2032):
        assert_energy(frozen, year, 100)
        assert frozen.dataset[year].energy_price_basis == DECLARATION
        for variable in ENERGY:
            np.testing.assert_array_equal(
                frozen.dataset[year].household[variable], [100.0, 0.0]
            )
    assert original.energy_price_basis == DECLARATION


def test_external_multi_year_amounts_are_authoritative():
    first = energy_dataset(DECLARATION)
    later = energy_dataset(
        {"period_type": "fiscal_year", "period_value": 2026}, year=2026
    )
    for variable in ENERGY:
        later.household[variable] = [777.0, 0.0]
    source = UKMultiYearDataset(datasets=[first, later])
    simulation = Simulation(dataset=source, scenario=before_load())
    assert_energy(simulation, 2024, 100)
    assert_energy(simulation, 2026, 777)
    assert simulation.dataset[2026].energy_price_basis == later.energy_price_basis


def test_external_dataframe_amounts_are_authoritative():
    frame = pd.DataFrame(
        {
            "person_id__2024": [1, 2],
            "person_benunit_id__2024": [1, 2],
            "person_household_id__2024": [1, 2],
            "age__2024": [40, 50],
            **{f"{variable}__2024": [100.0, 0.0] for variable in ENERGY},
            **{f"{variable}__2026": [777.0, 0.0] for variable in ENERGY},
        }
    )
    before = frame.copy(deep=True)
    simulation = Simulation(dataset=frame, scenario=before_load())
    assert_energy(simulation, 2024, 100)
    assert_energy(simulation, 2026, 777)
    pd.testing.assert_frame_equal(frame, before)


def test_direct_situation_uprates_by_the_fiscal_year_energy_index():
    simulation = Simulation(
        situation={
            "people": {"person": {"age": {2024: 40}}},
            "benunits": {"benunit": {"members": ["person"]}},
            "households": {
                "household": {
                    "members": ["person"],
                    **{variable: {2024: 100.0} for variable in ENERGY},
                }
            },
        },
        scenario=before_load(),
    )
    for variable in ENERGY:
        np.testing.assert_allclose(simulation.calculate(variable, 2026), [125.0])


def _controlled_energy_history(monkeypatch, history):
    """Real, clean index leaves with only the explicitly supplied history.

    Every series, calendar and fiscal year alike, gets the same history.
    """
    from policyengine_core.parameters import Parameter, ParameterNode
    from policyengine_uk.data import economic_assumptions

    name = "controlled_energy_index"
    parameters = ParameterNode("", data={})
    root = ParameterNode(name, data={})
    parameters.add_child(name, root)
    for kind in ("calendar_year", "fiscal_year"):
        node = ParameterNode(f"{name}.{kind}", data={})
        root.add_child(kind, node)
        for series in set(economic_assumptions.ENERGY_PRICE_SERIES.values()):
            node.add_child(
                series, Parameter(f"{name}.{kind}.{series}", data=dict(history))
            )
    monkeypatch.setattr(economic_assumptions, "ENERGY_PRICES", name)
    return parameters


def test_declared_energy_projection_ignores_widened_generic_exclusions(
    monkeypatch, parameters
):
    from policyengine_uk.data import economic_assumptions

    unrelated = "food_and_non_alcoholic_beverages_consumption"
    monkeypatch.setattr(
        economic_assumptions,
        "DATASET_UPRATING_EXCLUSIONS",
        economic_assumptions.DATASET_UPRATING_EXCLUSIONS | {unrelated},
    )
    observed = energy_dataset(DECLARATION)
    observed.household[unrelated] = [20.0, 30.0]
    current = observed.copy()
    current.time_period = "2026"
    current.household[unrelated] = [777.0, 888.0]
    before = observed.household.copy(deep=True)

    economic_assumptions.uprate_energy(current, observed, parameters)

    for variable in ENERGY:
        # Controlled annual index oracle: 100 * 125 / 100 = 125.
        np.testing.assert_array_equal(current.household[variable], [125.0, 0.0])
    np.testing.assert_array_equal(current.household[unrelated], [777.0, 888.0])
    assert current.energy_price_basis == {
        "period_type": "fiscal_year",
        "period_value": 2026,
    }
    pd.testing.assert_frame_equal(observed.household, before)
    assert observed.energy_price_basis == DECLARATION


@pytest.mark.parametrize(
    "first_supported,basis_year,target_year,unsupported_year",
    [
        pytest.param("2031-01-01", 2030, 2033, 2030, id="basis-before-first-value"),
        pytest.param("2031-01-01", 2033, 2030, 2030, id="target-before-first-value"),
        pytest.param("2031-07-01", 2031, 2033, 2031, id="basis-before-midyear-start"),
        pytest.param("2031-07-01", 2033, 2031, 2031, id="target-before-midyear-start"),
    ],
)
def test_energy_projection_rejects_pre_support_basis_and_target(
    monkeypatch, first_supported, basis_year, target_year, unsupported_year
):
    from policyengine_uk.data import economic_assumptions

    parameters = _controlled_energy_history(
        monkeypatch,
        {"2028-01-01": None, first_supported: 100, "2033-01-01": 125},
    )
    basis = {"period_type": "calendar_year", "period_value": basis_year}
    observed = energy_dataset(basis, year=2030)
    current = observed.copy()
    current.time_period = str(target_year)

    with pytest.raises(ValueError, match="controlled_energy_index") as error:
        economic_assumptions.uprate_energy(current, observed, parameters)
    assert f"{unsupported_year}-01-01" in str(error.value)
    assert first_supported in str(error.value)
    for variable in ENERGY:
        np.testing.assert_array_equal(observed.household[variable], [100.0, 0.0])
    assert observed.energy_price_basis == basis


@pytest.mark.parametrize(
    "first_supported,basis_year,target_year,expected",
    [
        pytest.param("2031-01-01", 2031, 2031, 100, id="first-supported-boundary"),
        pytest.param("2031-01-01", 2031, 2033, 125, id="valid-ratio"),
        pytest.param("2031-07-01", 2032, 2033, 125, id="after-midyear-start"),
        pytest.param(
            "2031-01-01", 2031, 2035, 125, id="existing-terminal-carry-forward"
        ),
    ],
)
def test_energy_projection_accepts_supported_boundary_and_future_ratio(
    monkeypatch, first_supported, basis_year, target_year, expected
):
    from policyengine_uk.data import economic_assumptions

    parameters = _controlled_energy_history(
        monkeypatch,
        {
            "2028-01-01": None,
            first_supported: 100,
            "2033-01-01": 125,
            "2034-01-01": None,
        },
    )
    basis = {"period_type": "calendar_year", "period_value": basis_year}
    observed = energy_dataset(basis, year=2030)
    current = observed.copy()
    current.time_period = str(target_year)

    economic_assumptions.uprate_energy(current, observed, parameters)

    for variable in ENERGY:
        np.testing.assert_array_equal(current.household[variable], [expected, 0.0])
        np.testing.assert_array_equal(observed.household[variable], [100.0, 0.0])
    assert current.energy_price_basis == {
        "period_type": "fiscal_year",
        "period_value": target_year,
    }
    assert observed.energy_price_basis == basis


@pytest.mark.parametrize(
    "history",
    [
        pytest.param({}, id="empty-history"),
        pytest.param({"2028-01-01": None, "2034-01-01": None}, id="all-null-history"),
    ],
)
def test_declared_energy_projection_rejects_unusable_index_history(
    monkeypatch, history
):
    from policyengine_uk.data import economic_assumptions

    parameters = _controlled_energy_history(monkeypatch, history)
    observed = energy_dataset(DECLARATION)
    current = observed.copy()
    current.time_period = "2026"

    with pytest.raises(ValueError, match="controlled_energy_index"):
        economic_assumptions.uprate_energy(current, observed, parameters)
    assert observed.energy_price_basis == DECLARATION


@pytest.mark.parametrize("energy_kind", ["unlabelled", "absent-energy"])
@pytest.mark.parametrize(
    "history",
    [
        pytest.param({}, id="empty-history"),
        pytest.param({"2034-01-01": None}, id="all-null-history"),
        pytest.param({"2034-07-01": 100}, id="later-support"),
    ],
)
def test_unlabelled_or_absent_energy_does_not_require_index_history(
    monkeypatch, energy_kind, history
):
    from policyengine_uk.data import economic_assumptions

    parameters = _controlled_energy_history(monkeypatch, history)
    observed = energy_dataset(None if energy_kind == "unlabelled" else DECLARATION)
    if energy_kind == "absent-energy":
        observed.household = observed.household.drop(columns=list(ENERGY))
    before = observed.household.copy(deep=True)
    for year in (2026, 2032):
        current = observed.copy()
        current.time_period = str(year)
        economic_assumptions.uprate_energy(current, observed, parameters)
        pd.testing.assert_frame_equal(current.household, before)
        assert current.energy_price_basis == observed.energy_price_basis
    pd.testing.assert_frame_equal(observed.household, before)


def test_energy_projection_validates_reformed_selected_index_history(monkeypatch):
    from policyengine_uk.data import economic_assumptions

    parameters = _controlled_energy_history(
        monkeypatch, {"2030-01-01": 100, "2033-01-01": 125}
    )
    reformed = parameters.clone()
    selected_index = reformed.get_child(
        f"{economic_assumptions.ENERGY_PRICES}.calendar_year.electricity"
    )
    # A parameter reform withdraws the two earliest years of this clean history.
    selected_index.update(period="year:2030:2", value=None)
    assert (
        min(
            item.instant_str
            for item in selected_index.values_list
            if item.value is not None
        )
        == "2032-01-01"
    )
    observed = energy_dataset(
        {"period_type": "calendar_year", "period_value": 2030}, year=2030
    )
    current = observed.copy()
    current.time_period = "2033"
    economic_assumptions.uprate_energy(current, observed, parameters)
    for variable in ENERGY:
        np.testing.assert_array_equal(current.household[variable], [125.0, 0.0])

    with pytest.raises(ValueError, match="controlled_energy_index"):
        economic_assumptions.uprate_energy(current.copy(), observed, reformed)
    assert (
        parameters.get_child(
            f"{economic_assumptions.ENERGY_PRICES}.calendar_year.electricity"
        )("2030-01-01")
        == 100
    )
    assert observed.energy_price_basis == {
        "period_type": "calendar_year",
        "period_value": 2030,
    }
