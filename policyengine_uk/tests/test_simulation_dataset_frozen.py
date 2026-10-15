"""Stored MOCK inputs must describe the same frozen data as calculations."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st
from policyengine_core.data import Dataset

import policyengine_uk.simulation as simulation_module
from policyengine_uk import Simulation
from policyengine_uk.data import UKSingleYearDataset
from policyengine_uk.data import economic_assumptions
from policyengine_uk.data.economic_assumptions import (
    DATASET_UPRATING_EXCLUSIONS,
    extend_single_year_dataset,
)
from policyengine_uk.data.filter_dataset import filter_dataset
from policyengine_uk.scenarios import no_economic_assumptions
from policyengine_uk.system import system


pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

BASE_YEAR = 2025
END_YEAR = 2028
UPRATING_INDICES = yaml.safe_load(
    (Path(economic_assumptions.__file__).parent / "uprating_indices.yaml").read_text()
)
INDEXED_INPUTS = {
    name
    for names in UPRATING_INDICES.values()
    for name in names
    if name in system.variables
}
FALLBACK_INPUTS = {
    name
    for name, variable in system.variables.items()
    if variable.uprating is not None
    and variable.value_type in (int, float)
    and name not in INDEXED_INPUTS
    and name not in DATASET_UPRATING_EXCLUSIONS
}
UPRATED_INPUTS = INDEXED_INPUTS | FALLBACK_INPUTS | {"rent", "council_tax"}
# Simulation transfers these survey observations to their reported or
# pre-response input names after the loader has installed the arrays.
LOADED_INPUT_NAMES = {
    "employment_income": "employment_income_before_lsr",
    "capital_gains": "capital_gains_before_response",
    "employee_pension_contributions": "employee_pension_contributions_reported",
    "bus_fare_spending": "bus_fare_spending_reported",
}
GROWTH_PATHS = (
    "gov.economic_assumptions.yoy_growth.obr.average_earnings",
    "gov.economic_assumptions.yoy_growth.obr.consumer_price_index",
    "gov.economic_assumptions.yoy_growth.obr.per_capita.gdp",
    "gov.economic_assumptions.yoy_growth.obr.per_capita.mixed_income",
    "gov.economic_assumptions.yoy_growth.ons.population",
    "gov.economic_assumptions.yoy_growth.obr.council_tax.england",
    "gov.economic_assumptions.yoy_growth.ons.private_rental_prices.LONDON",
)


@pytest.fixture
def single_year():
    """One synthetic household with every model-defined uprated input."""
    single = UKSingleYearDataset(
        person=pd.DataFrame(
            {
                "person_id": [1],
                "person_benunit_id": [1],
                "person_household_id": [1],
                "age": [40],
                "employment_income": [30_000.0],
                "self_employment_income": [2_000.0],
                "savings_interest_income": [100.0],
                "capital_gains_before_response": [1_000.0],
                "childcare_expenses": [500.0],
                # filter_dataset can carry these without calculating taxes
                # and benefits just to impute population-wide values.
                "months_since_last_birthday": [3],
                "attends_private_school": [False],
            }
        ),
        benunit=pd.DataFrame(
            {"benunit_id": [1], "benunit_reported_capital": [5_000.0]}
        ),
        household=pd.DataFrame(
            {
                "household_id": [1],
                "household_weight": [1_000.0],
                "region": ["LONDON"],
                "tenure_type": ["RENT_PRIVATELY"],
                "rent": [12_000.0],
                "council_tax": [1_500.0],
                "mortgage_interest_repayment": [200.0],
                "food_and_non_alcoholic_beverages_consumption": [2_000.0],
            }
        ),
        fiscal_year=BASE_YEAR,
    )
    # Derive coverage from the public index mapping and variable metadata,
    # including inputs whose own index only applies after the legacy horizon.
    tables = {
        name: getattr(single, name).to_dict(orient="list")
        for name in single.table_names
    }
    for name in sorted(UPRATED_INPUTS):
        variable = system.variables[name]
        amount = 1_000 if variable.value_type is int else 1_000.0
        tables[variable.entity.key].setdefault(name, [amount])
    for donor, target in LOADED_INPUT_NAMES.items():
        entity = system.variables[donor].entity.key
        tables[entity][target] = tables[entity][donor].copy()
    return UKSingleYearDataset(
        **{name: pd.DataFrame(values) for name, values in tables.items()},
        fiscal_year=BASE_YEAR,
    )


def _project(single_year, growth_changes=None):
    parameters = simulation_module.CountryTaxBenefitSystem().parameters.clone()
    for path, growth in (growth_changes or {}).items():
        parameters.get_child(path).update(period="2026", value=growth)
    projected = extend_single_year_dataset(single_year, parameters, end_year=END_YEAR)
    # Annual demographic inputs are authoritative independently of economic
    # assumptions. Give the fixture changing ages so the reset must retain them.
    for year in projected.years:
        projected[year].person = projected[year].person.assign(
            age=single_year.person.age + year - BASE_YEAR
        )
    projected._cgt_extension_provenance = {
        "capital_gains_before_response": {
            str(year): {
                "status": "projected",
                "method": "dataset_extension",
                "source_period": str(year - 1),
                "projection_fingerprint": None,
            }
            for year in projected.years[1:]
        }
    }
    return projected


def _build_frozen(monkeypatch, tmp_path, single_year, projected, route):
    restored_from = []
    restore = Simulation._restore_cgt_extension_provenance

    def capture_restore(self, dataset):
        restored_from.append(dataset)
        restore(self, dataset)

    monkeypatch.setattr(
        Simulation, "_restore_cgt_extension_provenance", capture_restore
    )
    if route in ("hf-cache", "gs-cache"):
        scheme = "hf" if route == "hf-cache" else "gs"
        source = f"{scheme}://mock/frozen-inputs/dataset.h5"
        monkeypatch.setattr(
            simulation_module, "_url_dataset_cache", {source: projected}
        )
        # #2405 prevents ordinary frozen simulations from reusing this cache.
        # Force the historical route to test the caller's ownership of the
        # real multi-year loader's reset copy independently of cache policy.
        monkeypatch.setattr(Simulation, "_dataset_cache_key", lambda self, url: url)

        def unexpected_download(*args, **kwargs):
            pytest.fail("The MOCK URL must load from the seeded in-memory cache")

        monkeypatch.setattr(
            simulation_module, "download_huggingface_dataset", unexpected_download
        )
        monkeypatch.setattr(
            simulation_module, "materialize_gcs_dataset_url", unexpected_download
        )
    else:
        # The scenario normally freezes growth before extension. Supplying a
        # genuinely projected extension exercises reset in these callers too;
        # the multi-year builder and reset_growthfactor_uprating are real.
        monkeypatch.setattr(
            Simulation,
            "_extend_dataset_with_cgt_provenance",
            lambda self, dataset: projected,
        )
        if route == "single-year":
            source = single_year
        elif route == "file":
            source = tmp_path / "single-year.h5"
            single_year.save(str(source))
        else:
            assert route == "core-dataset"
            dataset_path = tmp_path / "core-dataset.h5"

            class MockCoreDataset(Dataset):
                name = "mock-frozen-inputs"
                label = "MOCK frozen input regression"
                data_format = Dataset.TIME_PERIOD_ARRAYS
                file_path = dataset_path

            source = MockCoreDataset()
            source.save_dataset(
                {
                    column: {str(BASE_YEAR): table[column].to_numpy()}
                    for table in single_year.tables
                    for column in table.columns
                    if table[column].dtype.kind in "biuf"
                }
            )

    sim = Simulation(dataset=source, scenario=no_economic_assumptions)
    # The scenario also builds a current-law baseline through this route.
    assert restored_from and all(original is projected for original in restored_from)
    return sim


def _assert_inputs_match(sim, base):
    supplied = {name for table in base.tables for name in table.columns}
    assert UPRATED_INPUTS <= supplied
    assert sim.dataset.years == list(range(BASE_YEAR, END_YEAR + 1))
    for year in sim.dataset.years:
        for table_name in base.table_names:
            table = getattr(sim.dataset[year], table_name)
            base_table = getattr(base, table_name)
            for variable in sorted(set(base_table.columns) & UPRATED_INPUTS):
                calculated_variable = LOADED_INPUT_NAMES.get(variable, variable)
                calculated = np.asarray(sim.calculate(calculated_variable, year))
                np.testing.assert_allclose(
                    table[variable].to_numpy(),
                    calculated,
                    rtol=1e-6,
                    err_msg=f"{variable} in {year}: stored data differs from loaded inputs",
                )
                np.testing.assert_allclose(
                    table[variable].to_numpy(),
                    base_table[variable].to_numpy(),
                    rtol=1e-6,
                    err_msg=f"{variable} in {year}: economic growth was not reset",
                )


@pytest.mark.parametrize(
    "route", ["single-year", "file", "hf-cache", "gs-cache", "core-dataset"]
)
def test_frozen_dataset_matches_loaded_inputs(
    monkeypatch, tmp_path, single_year, route
):
    projected = _project(single_year)
    projected_income = projected[END_YEAR].person.employment_income.copy()
    assert projected_income.iloc[0] != single_year.person.employment_income.iloc[0]

    sim = _build_frozen(monkeypatch, tmp_path, single_year, projected, route)

    _assert_inputs_match(sim, single_year)
    assert sim.dataset is not projected
    pd.testing.assert_series_equal(
        projected[END_YEAR].person.employment_income, projected_income
    )
    # Provenance is restored from the original even though the reset copy
    # deliberately does not carry its private extension annotation.
    record = sim.capital_gains_projection_metadata["application"]["by_variable"][
        "capital_gains_before_response"
    ][str(END_YEAR)]
    assert record["status"] == "unknown"
    assert record["projection_fingerprint"] is None


@settings(
    max_examples=8,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@example(growth_changes={GROWTH_PATHS[0]: 0.2})
@given(
    growth_changes=st.dictionaries(
        st.sampled_from(GROWTH_PATHS),
        st.floats(min_value=-0.4, max_value=0.6, allow_nan=False, allow_infinity=False),
        min_size=1,
        max_size=len(GROWTH_PATHS),
    )
)
def test_frozen_dataset_matches_loaded_inputs_for_random_growth(
    monkeypatch, tmp_path, single_year, growth_changes
):
    projected = _project(single_year, growth_changes)
    with monkeypatch.context() as patch:
        sim = _build_frozen(patch, tmp_path, single_year, projected, "hf-cache")
        _assert_inputs_match(sim, single_year)


def test_filter_dataset_uses_frozen_inputs(monkeypatch, tmp_path, single_year):
    projected = _project(single_year)
    sim = _build_frozen(monkeypatch, tmp_path, single_year, projected, "hf-cache")

    extracted = filter_dataset(sim, household_id=1, year=END_YEAR)

    assert extracted.time_period == str(END_YEAR)
    np.testing.assert_array_equal(
        extracted.person.age, single_year.person.age + END_YEAR - BASE_YEAR
    )
    for table_name in single_year.table_names:
        table = getattr(extracted, table_name)
        base_table = getattr(single_year, table_name)
        for variable in base_table.select_dtypes(include="number"):
            if variable == "age":
                continue
            np.testing.assert_allclose(table[variable], base_table[variable], rtol=1e-6)
