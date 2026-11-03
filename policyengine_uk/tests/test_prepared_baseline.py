"""Prepared baseline reuse must match fresh construction on synthetic local data.

The public file deliberately stores every year queried by these tests. No
certified dataset, remote source, or national performance measurement is used.
"""

from pathlib import Path
import json
import shutil
from tempfile import TemporaryDirectory
from unittest.mock import Mock
from importlib import metadata

from hypothesis import example, given, settings
from hypothesis import strategies as st

import h5py

import numpy as np
import pandas as pd
import pytest

from policyengine_uk import Microsimulation, Simulation
from policyengine_uk.data.dataset_schema import UKMultiYearDataset, UKSingleYearDataset
from policyengine_uk.data.isa_income import ISA_INCOME_CONTRACT_KEY
from policyengine_uk.data.savings_income_projection import SAVINGS_INCOME_PROJECTION_KEY
from policyengine_core.reforms import Reform
from policyengine_uk.data.capital_gains_projection import CapitalGainsProjection
from policyengine_uk.model_api import Scenario, Variable, Person, YEAR


YEARS = (2025, 2026, 2028)
VAT = "gov.hmrc.vat.standard_rate"
OUTPUTS = (
    "employment_income_before_lsr",
    "income_tax",
    "ni_class_1_employee",
    "universal_credit",
    "household_net_income",
)


def local_data(path: Path, families=None, *, gains=False) -> Path:
    """Two independent parent-child families, five explicitly stored years."""
    families = [(30_000, True), (18_000, True)] if families is None else families
    people, units, homes, ages, parent_flags, earnings = [], [], [], [], [], []
    for index, (income, child) in enumerate(families):
        unit, home = 11 * (index + 1), 101 * (index + 1)
        for is_child in [False, True] if child else [False]:
            people.append(len(people) + 1)
            units.append(unit)
            homes.append(home)
            ages.append(5 + 3 * index if is_child else 40 + 5 * index)
            parent_flags.append(not is_child)
            earnings.append(0.0 if is_child else float(income))
    unit_ids = list(dict.fromkeys(units))
    home_ids = list(dict.fromkeys(homes))
    datasets = []
    for year in range(2024, 2029):
        person = pd.DataFrame(
            {
                "person_id": people,
                "person_benunit_id": units,
                "person_household_id": homes,
                "age": ages,
                "is_parent": parent_flags,
                "employment_income": earnings,
                "employee_pension_contributions": [0.0] * len(people),
                "capital_gains_before_response": [
                    1000.0 if gains and i == 0 else 0.0 for i in range(len(people))
                ],
            }
        )
        benunit = pd.DataFrame(
            {"benunit_id": unit_ids, "would_claim_uc": [False] * len(unit_ids)}
        )
        household = pd.DataFrame(
            {
                "household_id": home_ids,
                "household_weight": [1.0] * len(home_ids),
                "region": ["LONDON"] * len(home_ids),
                "tenure_type": ["OWNED_OUTRIGHT"] * len(home_ids),
                "rent": [0.0] * len(home_ids),
                "council_tax": [0.0] * len(home_ids),
                "full_rate_vat_consumption": [
                    10_000.0 if i == 0 else 4_000.0 for i in range(len(home_ids))
                ],
                "reduced_rate_vat_consumption": [0.0] * len(home_ids),
            }
        )
        datasets.append(
            UKSingleYearDataset(
                person=person,
                benunit=benunit,
                household=household,
                fiscal_year=year,
            )
        )
    multi = UKMultiYearDataset(datasets=datasets)
    # Fixed-format pandas groups are accepted by the same public loader and
    # avoid per-column index overhead on these tiny five-year tables.
    with pd.HDFStore(path, mode="w", complevel=9, complib="zlib") as store:
        for data in datasets:
            year = int(data.time_period)
            for entity in ("person", "benunit", "household"):
                store.put(f"{entity}/{year}", getattr(data, entity), format="fixed")
            store.put(f"time_period/{year}", pd.Series([year]), format="fixed")
    with h5py.File(path, "a") as output:
        output.attrs[ISA_INCOME_CONTRACT_KEY] = json.dumps(multi.isa_income_contract)
        output.attrs[SAVINGS_INCOME_PROJECTION_KEY] = multi.savings_income_projection
    assert path.stat().st_size <= 2 * 1024 * 1024
    return path


def values(simulation, variable, year):
    return np.asarray(simulation.calculate(variable, year)).copy()


def snapshot(simulation, years=YEARS):
    return {
        (side, variable, year): values(world, variable, year)
        for side, world in (("reform", simulation), ("baseline", simulation.baseline))
        for year in years
        for variable in OUTPUTS
    }


def assert_same_snapshot(actual, expected):
    assert actual.keys() == expected.keys()
    for key in actual:
        np.testing.assert_allclose(actual[key], expected[key], rtol=1e-6, atol=0.01)


def test_fresh_reference_fixture_control(tmp_path):
    """The existing constructor works before any new prepared API exists."""
    path = local_data(tmp_path / "public-tiny.h5")
    simulation = Simulation(dataset=path)
    for year in YEARS:
        np.testing.assert_allclose(
            values(simulation, "employment_income_before_lsr", year),
            [30_000, 0, 18_000, 0],
            atol=0.01,
        )
    # Ordinary non-savings earnings: (30,000 - 12,570) * .20 and
    # (18,000 - 12,570) * .20. No pension contribution, gain or other income.
    np.testing.assert_allclose(
        values(simulation, "income_tax", 2025), [3_486, 0, 1_086, 0], atol=0.01
    )
    assert all(np.isfinite(array).all() for array in snapshot(simulation).values())
    np.testing.assert_array_equal(simulation.person.ids, [1, 2, 3, 4])
    np.testing.assert_array_equal(simulation.household.ids, [101, 202])


def test_prepared_matches_fresh_ordinary_parameter(tmp_path):
    """Only this body reaches the new API in the two-case initial baseline."""
    path = local_data(tmp_path / "public-tiny.h5")
    scenario = Scenario(parameter_changes={VAT: 0.22})
    fresh = Simulation(dataset=path, scenario=scenario)
    expected = snapshot(fresh)
    # Keep the lookup inside the body: an absent API is a legitimate feature
    # TDD failure, not a collection/import failure or a financial regression.
    prepared = Simulation.prepare_baseline(dataset=path)
    reused = Simulation(dataset=path, scenario=scenario, prepared_baseline=prepared)
    assert_same_snapshot(snapshot(reused), expected)
    assert (
        reused.tax_benefit_system.parameters.gov.hmrc.vat.standard_rate("2026") == 0.22
    )
    assert (
        reused.baseline.tax_benefit_system.parameters.gov.hmrc.vat.standard_rate("2026")
        == 0.20
    )
    assert (values(reused, "vat", 2026) > values(reused.baseline, "vat", 2026)).all()


PERSONAL_ALLOWANCE = "gov.hmrc.income_tax.allowances.personal_allowance.amount"


def projection():
    return CapitalGainsProjection(
        name="prepared-baseline-test",
        base_year=2024,
        annual_growth={year: 0.10 for year in range(2025, 2029)},
        source="Synthetic engineering fixture",
        vintage="test",
        assumptions="Common growth for synthetic gains",
    )


def zero_tax_reform():
    class income_tax(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR

        def formula(person, period, parameters):
            return person.filled_array(0)

    class zero_income_tax(Reform):
        def apply(self):
            self.update_variable(income_tax)

    return zero_income_tax


def route(name, events):
    def record(stage, *, edit=False):
        def modifier(simulation):
            events.append((stage, hasattr(simulation, "populations")))
            if edit:
                for year in YEARS:
                    simulation.set_input(
                        "private_pension_income", year, [1000, 0, 500, 0]
                    )

        return modifier

    if name == "dated_reform":
        return Scenario.from_reform({VAT: {"2026": 0.22}})
    if name == "before_load_structural":
        return Scenario.from_reform(zero_tax_reform()).model_copy(
            update={"applied_before_data_load": True}
        )
    if name == "after_load_input_modifier":
        return Scenario(simulation_modifier=record("after", edit=True))
    if name == "ordered_mixed_scenario":
        return Scenario(
            parameter_changes={VAT: 0.22},
            simulation_modifier=record("before"),
            applied_before_data_load=True,
        ) + Scenario(simulation_modifier=record("after", edit=True))
    if name == "uprating_change":
        return Scenario(
            parameter_changes={
                "gov.economic_assumptions.yoy_growth.obr.average_earnings": {
                    "2026": 0.03
                }
            },
            applied_before_data_load=True,
        )
    return Scenario(parameter_changes={VAT: 0.22})


@pytest.mark.parametrize(
    "name",
    [
        "dated_reform",
        "before_load_structural",
        "after_load_input_modifier",
        "ordered_mixed_scenario",
        "uprating_change",
        "microsimulation_custom_cgt",
    ],
)
def test_other_routes_match_fresh(tmp_path, name):
    is_micro = name == "microsimulation_custom_cgt"
    path = local_data(tmp_path / "route.h5", gains=is_micro)
    cls = Microsimulation if is_micro else Simulation
    options = (
        {"trace": True, "capital_gains_projection": projection()} if is_micro else {}
    )
    fresh_events = []
    fresh = cls(dataset=path, scenario=route(name, fresh_events), **options)
    expected = snapshot(fresh)
    if is_micro:
        # Save the complete independent reference, then end its lifetime
        # before constructing the preparation and reuse worlds. No forced GC.
        fresh_ids = (
            np.asarray(fresh.person.ids).copy(),
            np.asarray(fresh.household.ids).copy(),
        )
        fresh_gains = {
            year: values(fresh.baseline, "capital_gains_before_response", year)
            for year in YEARS
        }
        fresh_tracer = fresh.baseline.tracer
        del fresh
    prepared = cls.prepare_baseline(dataset=path, **options)
    events = []
    reused = cls(
        dataset=path,
        scenario=route(name, events),
        prepared_baseline=prepared,
        **options,
    )
    assert_same_snapshot(snapshot(reused), expected)
    assert events == fresh_events
    np.testing.assert_array_equal(
        reused.person.ids, fresh_ids[0] if is_micro else fresh.person.ids
    )
    np.testing.assert_array_equal(
        reused.household.ids, fresh_ids[1] if is_micro else fresh.household.ids
    )
    assert type(reused.baseline) is Simulation
    assert reused.changed_from_baseline and not reused.baseline.changed_from_baseline
    if name == "before_load_structural":
        assert (values(reused, "income_tax", 2026) == 0).all()
        assert (values(reused.baseline, "income_tax", 2026) > 0).any()
    if name == "ordered_mixed_scenario":
        assert events == [("before", False), ("after", True)]
    if is_micro:
        for year in YEARS:
            np.testing.assert_allclose(
                values(reused.baseline, "capital_gains_before_response", year),
                fresh_gains[year],
                atol=0.01,
            )
            assert values(reused.baseline, "capital_gains_before_response", year)[0] > 0
        assert reused.baseline.tracer is not fresh_tracer


def test_preparation_avoids_nested_current_law_construction(tmp_path, monkeypatch):
    path = local_data(tmp_path / "constructor.h5")
    prepared = Simulation.prepare_baseline(dataset=path)
    original = Simulation.__init__
    calls = []

    def recorded(self, *args, **kwargs):
        calls.append((kwargs.get("scenario"), kwargs.get("reform")))
        original(self, *args, **kwargs)

    monkeypatch.setattr(Simulation, "__init__", recorded)
    fresh = Simulation(dataset=path, scenario=Scenario(parameter_changes={VAT: 0.22}))
    expected = snapshot(fresh)
    assert sum(scenario is None and reform is None for scenario, reform in calls) == 1
    calls.clear()
    for _ in range(2):
        reused = Simulation(
            dataset=path,
            scenario=Scenario(parameter_changes={VAT: 0.22}),
            prepared_baseline=prepared,
        )
        assert_same_snapshot(snapshot(reused), expected)
    assert len(calls) == 2
    assert not any(scenario is None and reform is None for scenario, reform in calls)


@pytest.mark.parametrize(
    "kind",
    ["inputs_arrays", "parameters_variables", "dataset_metadata", "IDs_branches_inner"],
)
def test_reuses_isolate_mutable_state(tmp_path, kind):
    path = local_data(tmp_path / "isolation.h5")
    prepared = Simulation.prepare_baseline(dataset=path)

    def consume():
        return Simulation(
            dataset=path,
            scenario=Scenario(parameter_changes={VAT: 0.22}),
            prepared_baseline=prepared,
        )

    first, sibling = consume(), consume()
    expected = snapshot(sibling)
    base = first.baseline
    inner_expected = values(
        sibling.baseline.baseline, "employment_income_before_lsr", 2026
    )
    if kind == "inputs_arrays":
        assert not np.shares_memory(
            base.calculate("employment_income_before_lsr", 2026),
            sibling.baseline.calculate("employment_income_before_lsr", 2026),
        )
        base.set_input("employment_income_before_lsr", 2026, [50_000, 0, 18_000, 0])
        base.drop_computed_arrays()
        assert not np.shares_memory(
            base.calculate("income_tax", 2026),
            sibling.baseline.calculate("income_tax", 2026),
        )
    elif kind == "parameters_variables":
        base.apply_reform(zero_tax_reform())
        base.tax_benefit_system.parameters.get_child(VAT).update(
            period="year:2026:1", value=0.40
        )
        base.tax_benefit_system.reset_parameter_caches()
        base.drop_computed_arrays()
        assert (values(base, "income_tax", 2026) == 0).all()
        assert (values(sibling.baseline, "income_tax", 2026) > 0).any()
    elif kind == "dataset_metadata":
        base.dataset[2026].person.loc[0, "employment_income"] = 99_999
        base.dataset[2026].person.attrs["test_nested_metadata"] = {"values": [1]}
        base.input_variables.append("test_sentinel")
        base.calculated_periods.append("test_sentinel")
        assert "test_sentinel" not in sibling.baseline.input_variables
        assert "test_sentinel" not in sibling.baseline.calculated_periods
    else:
        original_ids = np.asarray(sibling.baseline.person.ids).copy()
        base.person.ids[0] = 999
        base.benunit.members_entity_id[0] = 1
        branch = base.get_branch("owned-test")
        branch.set_input("employment_income_before_lsr", 2026, [60_000, 0, 18_000, 0])
        base.baseline.set_input(
            "employment_income_before_lsr", 2026, [70_000, 0, 18_000, 0]
        )
        np.testing.assert_array_equal(sibling.baseline.person.ids, original_ids)
        assert "owned-test" not in sibling.baseline.branches
    assert_same_snapshot(snapshot(sibling), expected)
    np.testing.assert_allclose(
        values(sibling.baseline.baseline, "employment_income_before_lsr", 2026),
        inner_expected,
    )
    later = consume()
    assert_same_snapshot(snapshot(later), expected)
    np.testing.assert_array_equal(later.baseline.person.ids, [1, 2, 3, 4])
    assert later.baseline.dataset[2026].person.employment_income.iloc[0] == 30_000
    assert "test_nested_metadata" not in later.baseline.dataset[2026].person.attrs
    assert "test_sentinel" not in later.baseline.input_variables
    assert "test_sentinel" not in later.baseline.calculated_periods
    assert "owned-test" not in later.baseline.branches
    assert first.baseline is not sibling.baseline
    assert first.baseline.baseline is not sibling.baseline.baseline


@pytest.mark.parametrize(
    "kind",
    [
        "file_bytes",
        "model_source",
        "UK_version",
        "Core_identity",
        "CGT",
        "options_calendar",
        "unsupported_source",
        "invalid_token_metadata",
    ],
)
def test_incompatible_prepared_fails_before_reuse(tmp_path, monkeypatch, kind):
    import policyengine_uk.utils.prepared_baseline as helper
    import policyengine_uk.utils.aggregate_impact.measure as measure
    import policyengine_uk.tax_benefit_system as tax_system

    path = local_data(tmp_path / "identity.h5")
    prepared = Simulation.prepare_baseline(dataset=path)
    scenario = Scenario(parameter_changes={VAT: 0.22})

    def rejected(**kwargs):
        options = {"dataset": path, "scenario": scenario, "prepared_baseline": prepared}
        options.update(kwargs)
        with pytest.raises(ValueError) as error:
            Simulation(**options)
        assert str(error.value)

    if kind == "file_bytes":
        with h5py.File(path, "a") as data:
            data.attrs["test_content_identity"] = "changed"
        rejected()
    elif kind == "model_source":
        monkeypatch.setattr(measure, "model_fingerprint", lambda: "different-model")
        rejected()
    elif kind == "UK_version":
        version = metadata.version
        monkeypatch.setattr(
            metadata,
            "version",
            lambda name: (
                version(name) + "-changed"
                if name == "policyengine-uk"
                else version(name)
            ),
        )
        rejected()
    elif kind == "Core_identity":
        version = metadata.version
        with monkeypatch.context() as patch:
            patch.setattr(
                metadata,
                "version",
                lambda name: (
                    version(name) + "-changed"
                    if name == "policyengine-core"
                    else version(name)
                ),
            )
            rejected()
        monkeypatch.setattr(helper, "_core_fingerprint", lambda: "different-core-code")
        rejected()
    elif kind == "CGT":
        rejected(capital_gains_projection=projection())
    elif kind == "options_calendar":
        rejected(trace=True)
        for name in ("default_input_period", "default_calculation_period"):
            with monkeypatch.context() as patch:
                patch.setattr(Simulation, name, getattr(Simulation, name) + 1)
                rejected()
        predicate = tax_system.parameter_reads_calendar_years()
        monkeypatch.setattr(
            tax_system,
            "parameter_reads_calendar_years",
            lambda: (
                lambda name: not predicate(name) if name == VAT else predicate(name)
            ),
        )
        rejected()
    elif kind == "unsupported_source":
        same_bytes = tmp_path / "different-path.h5"
        shutil.copyfile(path, same_bytes)
        rejected(dataset=same_bytes)
        # Explicit unsupported sources must fail before any materializer or
        # builder can run. These strings identify no real remote data.
        fail = Mock(side_effect=AssertionError("unsupported source reached builder"))
        for method in (
            "build_from_dataset_source",
            "build_from_dataframe",
            "build_from_single_year_dataset",
            "build_from_multi_year_dataset",
            "build_from_situation",
        ):
            monkeypatch.setattr(Simulation, method, fail)
        monkeypatch.setenv(
            "POLICYENGINE_UK_DEFAULT_DATASET", "hf://synthetic/never-download.h5"
        )
        for dataset in (
            "hf://synthetic/never-download.h5",
            "gs://synthetic/never-download.h5",
            None,
            pd.DataFrame({"age": [40]}),
            UKMultiYearDataset(file_path=str(path)),
        ):
            rejected(dataset=dataset)
        rejected(dataset=None, situation={"people": {"adult": {"age": 40}}})
        fail.assert_not_called()
    else:
        raw = Simulation(dataset=path)
        for token in (object(), raw):
            rejected(prepared_baseline=token)
        bad = tmp_path / "invalid-metadata.h5"
        shutil.copyfile(path, bad)
        with h5py.File(bad, "a") as data:
            data.attrs[ISA_INCOME_CONTRACT_KEY] = json.dumps({"version": 999})
        with pytest.raises(ValueError):
            Simulation.prepare_baseline(dataset=bad)
        with pytest.raises(ValueError):
            Simulation(dataset=path, prepared_baseline=prepared)


def test_omitted_or_none_keeps_fresh_behavior(tmp_path):
    path = local_data(tmp_path / "none.h5")
    scenario = Scenario(parameter_changes={VAT: 0.22})
    omitted = Simulation(dataset=path, scenario=scenario)
    explicit_none = Simulation(dataset=path, scenario=scenario, prepared_baseline=None)
    assert_same_snapshot(snapshot(explicit_none), snapshot(omitted))


@settings(max_examples=6, deadline=None, derandomize=True, database=None)
@example(families=[(0, False)], year=2025, allowance=12_570)
@example(families=[(30_000, True)], year=2026, allowance=14_000)
@example(
    families=[(120_000, False), (20_000, True), (0, True)], year=2028, allowance=17_000
)
@given(
    families=st.lists(
        st.tuples(st.integers(0, 120_000), st.booleans()), min_size=1, max_size=3
    ),
    year=st.sampled_from(YEARS),
    allowance=st.integers(12_000, 18_000),
)
def test_prepared_differential_property(families, year, allowance):
    # A directory belongs to each example, not a function-scoped pytest
    # fixture. No health-check suppression or fixture reuse across examples.
    with TemporaryDirectory(prefix="prepared-baseline-public-") as directory:
        path = local_data(Path(directory) / "property.h5", families=families)
        scenario = Scenario(
            parameter_changes={PERSONAL_ALLOWANCE: {str(year): allowance}}
        )
        fresh = Simulation(dataset=path, scenario=scenario)
        expected = snapshot(fresh, years=(year,))
        reference_wages = values(fresh.baseline, "employment_income_before_lsr", year)
        del fresh
        prepared = Simulation.prepare_baseline(dataset=path)
        reused = Simulation(dataset=path, scenario=scenario, prepared_baseline=prepared)
        assert_same_snapshot(snapshot(reused, years=(year,)), expected)
        branch = reused.baseline.get_branch("property-input")
        wages = values(branch, "employment_income_before_lsr", year)
        branch.set_input("employment_income_before_lsr", year, wages + 100)
        np.testing.assert_allclose(
            values(reused.baseline, "employment_income_before_lsr", year),
            reference_wages,
        )
        del branch, reused
        later = Simulation(dataset=path, scenario=scenario, prepared_baseline=prepared)
        assert_same_snapshot(snapshot(later, years=(year,)), expected)
