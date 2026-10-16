"""Group table rows name groups by identifier, independently in each year."""

import h5py
import numpy as np
import pandas as pd
import pytest
from policyengine_core.data import Dataset

from policyengine_uk import Microsimulation, Simulation
from policyengine_uk.data import UKMultiYearDataset, UKSingleYearDataset
from policyengine_uk.scenarios import no_economic_assumptions
from policyengine_uk.system import system

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

# A synthetic £100 monthly allowance for every claimant type makes the final
# award £1,200 when capital permits it, with no earnings, rent or deductions.
REFORM = {
    f"gov.dwp.universal_credit.standard_allowance.amount.{kind}": {
        2025: 100,
        2026: 100,
    }
    for kind in ["SINGLE_YOUNG", "SINGLE_OLD", "COUPLE_YOUNG", "COUPLE_OLD"]
}
REFORM.update(
    {
        f"gov.dwp.universal_credit.deductions.abolish.{kind}": {2025: True, 2026: True}
        for kind in ["advance", "third_party", "government"]
    }
)


def group_dataset(year=2025, benunits=(70, 10, 40), households=(900, 100)):
    person = pd.DataFrame(
        {
            "person_id": [303, 101, 202, 404],
            "person_benunit_id": [70, 10, 10, 40],
            "person_household_id": [900, 100, 100, 900],
            "age": [40, 40, 39, 50],
            "employment_income": 0.0,
        }
    )
    benunit = (
        pd.DataFrame(
            {
                "benunit_id": [10, 40, 70],
                "benunit_reported_capital": (
                    [0.0, 6_000.0, 20_000.0] if year == 2025 else [20_000.0, 0.0, 0.0]
                ),
                "would_claim_uc": True,
            }
        )
        .set_index("benunit_id", drop=False)
        .loc[list(benunits)]
    )
    household = (
        pd.DataFrame(
            {
                "household_id": [100, 900],
                "household_weight": [10.0, 20.0] if year == 2025 else [11.0, 21.0],
                "region": ["WALES", "LONDON"],
                "rent": 0.0,
                "tenure_type": "OWNED_OUTRIGHT",
                "council_tax": [1_100.0, 2_200.0],
            }
        )
        .set_index("household_id", drop=False)
        .loc[list(households)]
    )
    return UKSingleYearDataset(
        person=person, benunit=benunit, household=household, fiscal_year=year
    )


def core_dataset_file(dataset, path):
    """The Core time-period-array layout, with group arrays in table row order."""
    with h5py.File(path, "w") as file:
        for table in dataset.tables:
            for variable in table.columns:
                values = table[variable].to_numpy()
                possible_values = getattr(
                    system.variables[variable], "possible_values", None
                )
                if possible_values is not None:
                    values = np.asarray(possible_values.encode(values))
                file.create_dataset(f"{variable}/{dataset.time_period}", data=values)
    return path


def array(sim, variable, year, **kwargs):
    result = sim.calculate(variable, year, **kwargs)
    if hasattr(result, "decode_to_str"):
        return result.decode_to_str()
    return np.asarray(result)


def assert_group_values(sim, year=2025):
    np.testing.assert_array_equal(sim.populations["person"].ids, [303, 101, 202, 404])
    for entity, expected in [("benunit", [10, 40, 70]), ("household", [100, 900])]:
        np.testing.assert_array_equal(sim.populations[entity].ids, expected)
        np.testing.assert_array_equal(array(sim, f"{entity}_id", year), expected)
    np.testing.assert_array_equal(array(sim, "person_id", year), [303, 101, 202, 404])
    np.testing.assert_array_equal(
        array(sim, "person_benunit_id", year), [70, 10, 10, 40]
    )
    np.testing.assert_array_equal(
        array(sim, "region", year, map_to="person"),
        ["LONDON", "WALES", "WALES", "LONDON"],
    )
    weights = [10, 20] if year == 2025 else [11, 21]
    np.testing.assert_array_equal(array(sim, "household_weight", year), weights)
    np.testing.assert_array_equal(
        array(sim, "household_weight", year, map_to="person"),
        [weights[1], weights[0], weights[0], weights[1]],
    )
    capital = [0, 6_000, 20_000] if year == 2025 else [20_000, 0, 0]
    np.testing.assert_array_equal(array(sim, "benunit_reported_capital", year), capital)
    np.testing.assert_array_equal(
        array(sim, "benunit_reported_capital", year, map_to="person"),
        [capital[2], capital[0], capital[0], capital[1]],
    )
    expected_uc = [1_200, 1_200, 0] if year == 2025 else [0, 1_200, 1_200]
    np.testing.assert_allclose(array(sim, "universal_credit", year), expected_uc)


@pytest.mark.parametrize(
    "source", ["single", "multi", "single_h5", "multi_h5", "core", "core_h5"]
)
def test_unsorted_group_tables_keep_their_inputs(source, tmp_path):
    single = group_dataset()
    before = {name: getattr(single, name).copy() for name in single.table_names}
    multi = UKMultiYearDataset(datasets=[single])
    if source in ["single", "multi"]:
        dataset = single if source == "single" else multi
    elif source in ["single_h5", "multi_h5"]:
        dataset = tmp_path / "uk.h5"
        (single if source == "single_h5" else multi).save(dataset)
    else:
        dataset = core_dataset_file(single, tmp_path / "core.h5")
        if source == "core":
            dataset = Dataset.from_file(dataset)

    sim = Simulation(dataset=dataset, reform=REFORM)

    assert_group_values(sim)
    # Existing enum encoding may change storage; alignment must not reorder
    # caller tables or alter their public values and identifier dtypes.
    for name, frame in before.items():
        actual = getattr(single, name)
        pd.testing.assert_frame_equal(actual, frame, check_dtype=False)
        for column in frame.columns:
            if column.endswith("_id"):
                assert actual[column].dtype == frame[column].dtype


def test_each_year_aligns_its_own_group_row_order():
    multi = UKMultiYearDataset(
        datasets=[group_dataset(), group_dataset(2026, (40, 70, 10), (100, 900))]
    )
    sim = Microsimulation(dataset=multi, reform=REFORM)

    assert_group_values(sim, 2025)
    assert_group_values(sim, 2026)


def test_sorted_group_tables_keep_the_same_results():
    sim = Simulation(
        dataset=group_dataset(benunits=(10, 40, 70), households=(100, 900)),
        reform=REFORM,
    )

    assert_group_values(sim)


def test_person_dataframe_rows_keep_their_own_group_values():
    frame = pd.DataFrame(
        {
            "person_id__2025": [303, 101, 202, 404],
            "benunit_id__2025": [70, 10, 10, 40],
            "household_id__2025": [900, 100, 100, 900],
            "age__2025": [40, 40, 39, 50],
            "employment_income__2025": 0.0,
            "benunit_reported_capital__2025": [20_000.0, 0.0, 0.0, 6_000.0],
            "household_weight__2025": [20.0, 10.0, 10.0, 20.0],
            "region__2025": ["LONDON", "WALES", "WALES", "LONDON"],
            "tenure_type__2025": "OWNED_OUTRIGHT",
            "council_tax__2025": 0.0,
            "rent__2025": 0.0,
        }
    )
    before = frame.copy()
    sim = Simulation(dataset=frame, reform=REFORM)

    assert_group_values(sim)
    pd.testing.assert_frame_equal(frame, before)


def test_frozen_assumptions_align_each_year_before_reset():
    source = UKMultiYearDataset(
        datasets=[group_dataset(), group_dataset(2026, (40, 70, 10), (100, 900))]
    )
    before = source[2026].copy()
    sim = Simulation(dataset=source, scenario=no_economic_assumptions)

    for year in (2025, 2026):
        np.testing.assert_array_equal(array(sim, "household_id", year), [100, 900])
        np.testing.assert_array_equal(array(sim, "benunit_id", year), [10, 40, 70])
        np.testing.assert_array_equal(array(sim, "household_weight", year), [10, 20])
        np.testing.assert_array_equal(array(sim, "council_tax", year), [1_100, 2_200])
        np.testing.assert_array_equal(
            array(sim, "benunit_reported_capital", year), [0, 6_000, 20_000]
        )
    for name in before.table_names:
        pd.testing.assert_frame_equal(
            getattr(source[2026], name), getattr(before, name)
        )
