"""Only a completed survey bereavement split freezes BSP projection (#2381).

The WPA column is the producer's completed-split signal, including an all-zero
column. BSP rates remain fixed under the Bereavement Support Payment Regulations
2017, regulation 3; the legacy combined survey field retains its CPI treatment.
The controlled 10% annual growth below is a projection oracle, not a forecast.
"""

import h5py
import numpy as np
import pandas as pd
import pytest
from policyengine_core.data import Dataset
from policyengine_core.reforms import Reform

from policyengine_uk import CountryTaxBenefitSystem, Simulation
from policyengine_uk.data import UKMultiYearDataset, UKSingleYearDataset
from policyengine_uk.data.economic_assumptions import extend_single_year_dataset
from policyengine_uk.model_api import YEAR, Person, Variable
from policyengine_uk.scenarios import no_economic_assumptions
from policyengine_uk.system import system
from policyengine_uk.utils.scenario import Scenario

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

BSP = "bsp_reported"
WPA = "widowed_parents_allowance_reported"
WAR_WIDOW = "war_widows_pension_reported"
CPI = "gov.economic_assumptions.indices.obr.consumer_price_index"
CPI_GROWTH = "gov.economic_assumptions.yoy_growth.obr.consumer_price_index"
BASE_YEAR = 2024
AMOUNTS = {BSP: 100.0, WPA: 70.0, WAR_WIDOW: 60.0}


def bereavement_dataset(*, wpa=70.0, war_widow=True, year=BASE_YEAR):
    """Two unrelated adults, one claimant and one with no reported benefits."""
    person = {
        "person_id": [1, 2],
        "person_benunit_id": [1, 2],
        "person_household_id": [1, 2],
        "age": [40, 50],
        BSP: [AMOUNTS[BSP], 0.0],
    }
    if wpa is not None:
        person[WPA] = [wpa, 0.0]
    if war_widow:
        person[WAR_WIDOW] = [AMOUNTS[WAR_WIDOW], 0.0]
    return UKSingleYearDataset(
        person=pd.DataFrame(person),
        benunit=pd.DataFrame({"benunit_id": [1, 2]}),
        household=pd.DataFrame(
            {
                "household_id": [1, 2],
                "region": ["LONDON", "WALES"],
                "tenure_type": ["OWNED_OUTRIGHT", "OWNED_OUTRIGHT"],
                "council_tax": [0.0, 0.0],
                "rent": [0.0, 0.0],
                "household_weight": [1.0, 2.0],
            }
        ),
        fiscal_year=year,
    )


def controlled_changes():
    return {
        CPI: {
            f"year:{year}-01-01:1": 100 * 1.1 ** (year - BASE_YEAR)
            for year in range(BASE_YEAR, 2036)
        },
        CPI_GROWTH: {f"year:{year}-01-01:1": 0.1 for year in range(BASE_YEAR, 2036)},
    }


@pytest.fixture(scope="module")
def controlled_parameters():
    parameters = CountryTaxBenefitSystem().parameters.clone()
    for name, periods in controlled_changes().items():
        for period, value in periods.items():
            parameters.get_child(name).update(period=period, value=value)
    return parameters


def controlled_scenario():
    return Scenario(
        parameter_changes=controlled_changes(), applied_before_data_load=True
    )


def assert_reported(simulation, name, year, amount):
    np.testing.assert_allclose(
        simulation.calculate(name, year), [amount, 0.0], rtol=1e-6
    )


@pytest.mark.parametrize("wpa", [70.0, 0.0], ids=["positive-wpa", "zero-wpa"])
def test_completed_split_freezes_bsp_in_each_projected_year(controlled_parameters, wpa):
    source = bereavement_dataset(wpa=wpa)
    before = source.person.copy(deep=True)
    projected = extend_single_year_dataset(source, controlled_parameters, end_year=2032)
    for year in (2024, 2029, 2032):
        np.testing.assert_array_equal(projected[year].person[BSP], [100.0, 0.0])
        factor = 1.1 ** (year - BASE_YEAR)
        np.testing.assert_allclose(projected[year].person[WPA], [wpa * factor, 0.0])
        np.testing.assert_allclose(
            projected[year].person[WAR_WIDOW], [60.0 * factor, 0.0]
        )
    pd.testing.assert_frame_equal(source.person, before)


@pytest.mark.parametrize("wpa", [70.0, 0.0], ids=["positive-wpa", "zero-wpa"])
def test_completed_split_freezes_bsp_after_the_projection_horizon(wpa):
    simulation = Simulation(
        dataset=bereavement_dataset(wpa=wpa), scenario=controlled_scenario()
    )
    for year in (2029, 2032, 2035):
        assert_reported(simulation, BSP, year, 100.0)
        factor = 1.1 ** (year - BASE_YEAR)
        assert_reported(simulation, WPA, year, wpa * factor)
        assert_reported(simulation, WAR_WIDOW, year, 60.0 * factor)


def test_wpa_column_alone_signals_the_completed_split():
    simulation = Simulation(
        dataset=bereavement_dataset(wpa=0.0, war_widow=False),
        scenario=controlled_scenario(),
    )
    for year in (2029, 2032, 2035):
        assert_reported(simulation, BSP, year, 100.0)


@pytest.mark.parametrize("war_widow", [False, True], ids=["legacy", "partial-split"])
def test_missing_wpa_column_preserves_legacy_cpi_uprating(war_widow):
    simulation = Simulation(
        dataset=bereavement_dataset(wpa=None, war_widow=war_widow),
        scenario=controlled_scenario(),
    )
    for year in (2024, 2029, 2032, 2035):
        factor = 1.1 ** (year - BASE_YEAR)
        assert_reported(simulation, BSP, year, 100.0 * factor)
        if war_widow:
            assert_reported(simulation, WAR_WIDOW, year, 60.0 * factor)


def test_calculating_default_wpa_does_not_migrate_a_legacy_dataset():
    simulation = Simulation(
        dataset=bereavement_dataset(wpa=None), scenario=controlled_scenario()
    )
    assert_reported(simulation, WPA, 2024, 0.0)
    assert_reported(simulation, WPA, 2035, 0.0)
    assert_reported(simulation, BSP, 2035, 100.0 * 1.1**11)


def core_arrays(source):
    arrays = {}
    for table in source.tables:
        for name in table.columns:
            values = table[name].to_numpy()
            possible_values = getattr(system.variables[name], "possible_values", None)
            if possible_values is not None:
                values = np.asarray(possible_values.encode(values))
            arrays[name] = {source.time_period: values}
    return arrays


class InMemoryCore(Dataset):
    """An already materialized, fixture-scale Core dataset."""

    def __init__(self, arrays):
        self.arrays = arrays

    def load_dataset(self):
        return self.arrays


@pytest.mark.parametrize("source_kind", ["single", "uk-h5", "core-h5", "core"])
@pytest.mark.parametrize("wpa", [None, 0.0], ids=["partial-split", "completed-split"])
def test_source_conversion_preserves_the_completed_split_signal(
    source_kind, wpa, tmp_path
):
    source = bereavement_dataset(wpa=wpa)
    if source_kind == "uk-h5":
        path = tmp_path / "bereavement.h5"
        source.save(path)
        source = path
    elif source_kind == "core-h5":
        path = tmp_path / "bereavement-core.h5"
        with h5py.File(path, "w") as file:
            for name, periods in core_arrays(source).items():
                for period, values in periods.items():
                    file.create_dataset(f"{name}/{period}", data=values)
        source = path
    elif source_kind == "core":
        source = InMemoryCore(core_arrays(source))
    simulation = Simulation(dataset=source, scenario=controlled_scenario())
    for year in (2029, 2032, 2035):
        expected = 100.0 if wpa is not None else 100.0 * 1.1 ** (year - BASE_YEAR)
        assert_reported(simulation, BSP, year, expected)
        assert_reported(simulation, WAR_WIDOW, year, 60.0 * 1.1 ** (year - BASE_YEAR))


def test_serialized_projected_child_retains_the_split_for_later_projection(
    controlled_parameters, tmp_path
):
    original = bereavement_dataset(wpa=0.0)
    projected = extend_single_year_dataset(
        original, controlled_parameters, end_year=2029
    )
    path = tmp_path / "projected-child.h5"
    projected[2029].save(path)
    simulation = Simulation(dataset=path, scenario=controlled_scenario())
    for year in (2029, 2032, 2035):
        assert_reported(simulation, BSP, year, 100.0)
        assert_reported(simulation, WAR_WIDOW, year, 60.0 * 1.1 ** (year - BASE_YEAR))
    np.testing.assert_array_equal(original.person[BSP], [100.0, 0.0])


@pytest.mark.parametrize("split_first", [False, True])
def test_split_and_legacy_simulations_and_their_clones_are_isolated(split_first):
    def build(wpa):
        return Simulation(
            dataset=bereavement_dataset(wpa=wpa), scenario=controlled_scenario()
        )

    if split_first:
        split, legacy = build(0.0), build(None)
    else:
        legacy, split = build(None), build(0.0)
    for simulation in (split, split.clone(), split.get_branch("split-child")):
        assert_reported(simulation, BSP, 2035, 100.0)
    for simulation in (legacy, legacy.clone(), legacy.get_branch("legacy-child")):
        assert_reported(simulation, BSP, 2035, 100.0 * 1.1**11)


def test_reform_and_baseline_both_recognize_the_completed_split():
    source = bereavement_dataset()
    reformed = Simulation(dataset=source, reform=controlled_changes())
    for year in (2029, 2032, 2035):
        assert_reported(reformed, BSP, year, 100.0)
        assert_reported(reformed.baseline, BSP, year, 100.0)
        assert_reported(reformed, WPA, year, 70.0 * 1.1 ** (year - BASE_YEAR))
    # The two CPI histories differ, so this proves the baseline remains distinct.
    assert reformed.calculate(WPA, 2029)[0] != pytest.approx(
        reformed.baseline.calculate(WPA, 2029)[0]
    )


def test_explicit_multiyear_bsp_values_remain_authoritative():
    first = bereavement_dataset()
    later = bereavement_dataset(year=2032)
    later.person[BSP] = [777.0, 0.0]
    source = UKMultiYearDataset(datasets=[first, later])
    before = later.person.copy(deep=True)
    simulation = Simulation(dataset=source, scenario=controlled_scenario())
    assert_reported(simulation, BSP, 2024, 100.0)
    assert_reported(simulation, BSP, 2032, 777.0)
    assert_reported(simulation, BSP, 2035, 777.0)
    pd.testing.assert_frame_equal(later.person, before)


@pytest.mark.parametrize(
    "first_split,later_split,expected",
    [
        (False, False, 100.0),
        (False, True, 777.0),
        (True, False, 777.0),
        (True, True, 777.0),
    ],
    ids=["both-legacy", "new-split", "later-without-wpa", "both-split"],
)
def test_no_economic_reset_preserves_separate_bsp_observations(
    first_split, later_split, expected
):
    first = bereavement_dataset(wpa=0.0 if first_split else None)
    later = bereavement_dataset(wpa=0.0 if later_split else None, year=2032)
    later.person[BSP] = [777.0, 0.0]
    source = UKMultiYearDataset(datasets=[first, later])
    simulation = Simulation(dataset=source, scenario=no_economic_assumptions)
    assert_reported(simulation, BSP, 2032, expected)
    np.testing.assert_array_equal(source[2032].person[BSP], [777.0, 0.0])


def household_situation(wpa):
    person = {"age": {2024: 40}, BSP: {2024: 100.0}}
    if wpa is not None:
        person[WPA] = {2024: wpa}
    return {
        "people": {"person": person},
        "benunits": {"benunit": {"members": ["person"]}},
        "households": {"household": {"members": ["person"]}},
    }


@pytest.mark.parametrize("wpa", [None, 0.0, 70.0])
def test_household_inputs_keep_cpi_treatment_even_with_explicit_wpa(wpa):
    simulation = Simulation(
        situation=household_situation(wpa), scenario=controlled_scenario()
    )
    for year in (2029, 2032, 2035):
        np.testing.assert_allclose(
            simulation.calculate(BSP, year),
            [100.0 * 1.1 ** (year - BASE_YEAR)],
            rtol=1e-6,
        )


def test_rebuilding_a_split_clone_as_a_household_drops_dataset_freeze():
    original = Simulation(
        dataset=bereavement_dataset(wpa=0.0), scenario=controlled_scenario()
    )
    assert_reported(original, BSP, 2035, 100.0)
    rebuilt = original.clone()
    rebuilt.build_from_situation(household_situation(wpa=0.0))
    np.testing.assert_allclose(
        rebuilt.calculate(BSP, 2035), [100.0 * 1.1**11], rtol=1e-6
    )
    assert_reported(original, BSP, 2035, 100.0)


def test_rebuilding_a_split_clone_as_legacy_data_drops_the_split_signal():
    original = Simulation(
        dataset=bereavement_dataset(wpa=0.0), scenario=controlled_scenario()
    )
    assert_reported(original, BSP, 2035, 100.0)
    rebuilt = original.clone()
    rebuilt.build_from_single_year_dataset(bereavement_dataset(wpa=None))
    assert_reported(rebuilt, BSP, 2035, 100.0 * 1.1**11)
    assert_reported(original, BSP, 2035, 100.0)


@pytest.mark.parametrize("month", ["2035-01", "2035-07"])
def test_split_bsp_beyond_the_horizon_is_divided_once_for_monthly_output(month):
    simulation = Simulation(
        dataset=bereavement_dataset(), scenario=controlled_scenario()
    )
    assert_reported(simulation, BSP, month, 100.0 / 12)
    assert_reported(simulation, BSP, 2035, 100.0)
    assert_reported(simulation, WPA, month, 70.0 * 1.1**11 / 12)


@pytest.mark.parametrize("override", ["neutralize", "formula"])
def test_split_bsp_fallback_respects_structural_variable_overrides(override):
    class bsp_reported(Variable):
        value_type = float
        entity = Person
        definition_period = YEAR
        label = "BSP (synthetic formula override)"
        uprating = None

        def formula(person, period, parameters):
            # A synthetic override deliberately pays the separately uprated WPA.
            return person("widowed_parents_allowance_reported", period)

    class change_bsp(Reform):
        def apply(self):
            if override == "neutralize":
                self.neutralize_variable(BSP)
            else:
                self.replace_variable(bsp_reported)

    simulation = Simulation(
        dataset=bereavement_dataset(), scenario=controlled_scenario()
    )
    assert_reported(simulation, BSP, 2035, 100.0)
    simulation.apply_reform(change_bsp)
    expected = 0.0 if override == "neutralize" else 70.0 * 1.1**11
    assert_reported(simulation, BSP, 2035, expected)


def test_branch_split_declaration_invalidates_previously_calculated_cpi_fallback():
    original = Simulation(
        dataset=bereavement_dataset(wpa=None), scenario=controlled_scenario()
    )
    assert_reported(original, BSP, 2035, 100.0 * 1.1**11)
    branch = original.get_branch("completed-split")
    assert_reported(branch, BSP, 2035, 100.0 * 1.1**11)
    # Equal to the calculated default, but now explicitly supplied in the BSP
    # source year. The provenance change alone declares a completed split.
    branch.set_input(WPA, 2032, [0.0, 0.0])
    assert_reported(branch, BSP, 2035, 100.0 * 1.1**8)
    assert_reported(original, BSP, 2035, 100.0 * 1.1**11)


def test_split_bsp_fallback_works_with_cache_opt_out():
    simulation = Simulation(
        dataset=bereavement_dataset(), scenario=controlled_scenario()
    )
    simulation.opt_out_cache = True
    simulation.tax_benefit_system.cache_blacklist = [BSP, WPA, WAR_WIDOW]
    for year in (2035, 2034, 2035):
        assert_reported(simulation, BSP, year, 100.0)
        assert_reported(simulation, WPA, year, 70.0 * 1.1 ** (year - BASE_YEAR))


def test_a_split_declaration_in_another_year_does_not_change_legacy_source_bsp():
    first = bereavement_dataset(wpa=0.0)
    later = bereavement_dataset(wpa=None, year=2032)
    later.person[BSP] = [777.0, 0.0]
    source = UKMultiYearDataset(datasets=[first, later])
    simulation = Simulation(dataset=source, scenario=controlled_scenario())
    assert_reported(simulation, BSP, 2035, 777.0 * 1.1**3)
