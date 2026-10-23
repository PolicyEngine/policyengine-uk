"""External energy observations retain a coherent amount group and price basis.

CPI levels 100/125/150 are controlled test inputs, not an economic forecast.
The later FY2026 observation must extend to 2027 by 150 / 125 after reset
and serialization; the original external observations must remain untouched.
"""

from copy import deepcopy
import json

import numpy as np
import pandas as pd
import pytest

from policyengine_uk import CountryTaxBenefitSystem, Simulation
from policyengine_uk.data import UKMultiYearDataset, UKSingleYearDataset
from policyengine_uk.data.economic_assumptions import extend_single_year_dataset
from policyengine_uk.scenarios import no_economic_assumptions

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

ENERGY = (
    "domestic_energy_consumption",
    "electricity_consumption",
    "gas_consumption",
)
LATER_BASIS = {"period_type": "fiscal_year", "period_value": 2026}


def _observation(year, amounts, basis):
    return UKSingleYearDataset(
        person=pd.DataFrame(
            {
                "person_id": [1],
                "person_benunit_id": [1],
                "person_household_id": [1],
                "age": [40],
            }
        ),
        benunit=pd.DataFrame({"benunit_id": [1]}),
        household=pd.DataFrame(
            {
                "household_id": [1],
                "region": ["LONDON"],
                "tenure_type": ["OWNED_OUTRIGHT"],
                "council_tax": [0.0],
                "rent": [0.0],
                "household_weight": [1.0],
                **{name: [value] for name, value in amounts.items()},
            }
        ),
        fiscal_year=year,
        energy_price_basis=basis,
    )


def _state(observation):
    return {
        "basis": deepcopy(observation.energy_price_basis),
        "amounts": {
            name: observation.household[name].tolist()
            for name in ENERGY
            if name in observation.household
        },
    }


@pytest.fixture
def controlled_parameters():
    parameters = CountryTaxBenefitSystem().parameters.clone()
    index = parameters.get_child(
        "gov.economic_assumptions.indices.obr.consumer_price_index"
    )
    for year, level in {2024: 100.0, 2026: 125.0, 2027: 150.0}.items():
        index.update(period=str(year), value=level)
    return parameters


@pytest.mark.parametrize(
    "base_amounts,base_basis,later_amounts",
    [
        ({}, None, dict.fromkeys(ENERGY, 777.0)),
        (
            {ENERGY[0]: 111.0},
            {"period_type": "calendar_year", "period_value": 2024},
            dict(zip(ENERGY, [777.0, 888.0, 999.0])),
        ),
    ],
    ids=["no-base-energy", "partial-base-different-basis"],
)
def test_external_energy_reset_survives_loading_and_extension(
    tmp_path, controlled_parameters, base_amounts, base_basis, later_amounts
):
    base = _observation(2024, base_amounts, base_basis)
    later = _observation(2026, later_amounts, LATER_BASIS)
    source = UKMultiYearDataset(datasets=[base, later])
    original = {
        year: {
            "state": _state(source[year]),
            "tables": [
                table.copy(deep=True)
                for table in (
                    source[year].person,
                    source[year].benunit,
                    source[year].household,
                )
            ],
        }
        for year in source.years
    }

    simulation = Simulation(dataset=source, scenario=no_economic_assumptions)
    child = simulation.dataset[2026]
    loaded_inputs = {name: simulation.calculate(name, 2026).tolist() for name in ENERGY}
    path = tmp_path / "external-child.h5"
    child.save(path)
    reloaded = UKSingleYearDataset(file_path=path)
    extended = extend_single_year_dataset(
        reloaded, controlled_parameters, end_year=2027
    )[2027]

    observations = {
        "caller_before": {year: item["state"] for year, item in original.items()},
        "caller_after": {year: _state(source[year]) for year in source.years},
        "reset_child": _state(child),
        "loaded_inputs_2026": loaded_inputs,
        "saved_reloaded_child": _state(reloaded),
        "extended_2027": _state(extended),
        "expected_2027": {
            name: [amount * 150.0 / 125.0] for name, amount in later_amounts.items()
        },
    }
    (tmp_path / "energy-reset-observations.json").write_text(
        json.dumps(observations, indent=2) + "\n"
    )

    # Check caller ownership even when the returned reset child is defective.
    for year in source.years:
        assert _state(source[year]) == original[year]["state"]
        for before, after in zip(
            original[year]["tables"],
            (source[year].person, source[year].benunit, source[year].household),
        ):
            # Public values stay exact; the loader may encode enum buffers.
            pd.testing.assert_frame_equal(before, after, check_dtype=False)

    for name, amount in later_amounts.items():
        np.testing.assert_array_equal(child.household[name], [amount])
        np.testing.assert_array_equal(loaded_inputs[name], [amount])
        np.testing.assert_array_equal(reloaded.household[name], [amount])
        # Hand oracle: 777 * 150 / 125 = 932.4, likewise 888 and 999.
        np.testing.assert_allclose(extended.household[name], [amount * 150.0 / 125.0])
    assert child.energy_price_basis == LATER_BASIS
    assert reloaded.energy_price_basis == LATER_BASIS
    assert extended.energy_price_basis == {
        "period_type": "fiscal_year",
        "period_value": 2027,
    }


# Each row states the retained observations explicitly. These expected amounts
# are hand oracles, not a second implementation of the reset decision.
@pytest.mark.parametrize(
    "base_amounts,base_basis,later_amounts,later_basis,"
    "expected_reset,expected_basis,expected_2027",
    [
        pytest.param(
            {ENERGY[1]: 222.0, ENERGY[2]: 333.0},
            {"period_type": "calendar_year", "period_value": 2024},
            dict(zip(ENERGY, [777.0, 888.0, 999.0])),
            LATER_BASIS,
            dict(zip(ENERGY, [777.0, 888.0, 999.0])),
            LATER_BASIS,
            dict(zip(ENERGY, [932.4, 1065.6, 1198.8])),
            id="two-base-columns-no-domestic-different-basis",
        ),
        pytest.param(
            {ENERGY[0]: 111.0, ENERGY[2]: 333.0},
            {"period_type": "calendar_year", "period_value": 2024},
            dict(zip(ENERGY, [777.0, 888.0, 999.0])),
            LATER_BASIS,
            dict(zip(ENERGY, [777.0, 888.0, 999.0])),
            LATER_BASIS,
            dict(zip(ENERGY, [932.4, 1065.6, 1198.8])),
            id="two-base-columns-no-electricity-different-basis",
        ),
        pytest.param(
            {ENERGY[0]: 111.0, ENERGY[1]: 222.0},
            {"period_type": "calendar_year", "period_value": 2024},
            dict(zip(ENERGY, [777.0, 888.0, 999.0])),
            LATER_BASIS,
            dict(zip(ENERGY, [777.0, 888.0, 999.0])),
            LATER_BASIS,
            dict(zip(ENERGY, [932.4, 1065.6, 1198.8])),
            id="two-base-columns-no-gas-different-basis",
        ),
        pytest.param(
            {ENERGY[0]: 111.0},
            LATER_BASIS,
            dict(zip(ENERGY, [777.0, 888.0, 999.0])),
            LATER_BASIS,
            dict(zip(ENERGY, [111.0, 888.0, 999.0])),
            LATER_BASIS,
            dict(zip(ENERGY, [133.2, 1065.6, 1198.8])),
            id="same-exact-basis-domestic-overlap-only",
        ),
        pytest.param(
            {ENERGY[1]: 111.0},
            LATER_BASIS,
            dict(zip(ENERGY, [777.0, 888.0, 999.0])),
            LATER_BASIS,
            dict(zip(ENERGY, [777.0, 111.0, 999.0])),
            LATER_BASIS,
            dict(zip(ENERGY, [932.4, 133.2, 1198.8])),
            id="same-exact-basis-electricity-overlap-only",
        ),
        pytest.param(
            {ENERGY[2]: 111.0},
            LATER_BASIS,
            dict(zip(ENERGY, [777.0, 888.0, 999.0])),
            LATER_BASIS,
            dict(zip(ENERGY, [777.0, 888.0, 111.0])),
            LATER_BASIS,
            dict(zip(ENERGY, [932.4, 1065.6, 133.2])),
            id="same-exact-basis-gas-overlap-only",
        ),
        pytest.param(
            dict(zip(ENERGY, [111.0, 222.0, 333.0])),
            {"period_type": "calendar_year", "period_value": 2024},
            dict(zip(ENERGY, [777.0, 888.0, 999.0])),
            LATER_BASIS,
            dict(zip(ENERGY, [111.0, 222.0, 333.0])),
            {"period_type": "calendar_year", "period_value": 2024},
            dict(zip(ENERGY, [166.5, 333.0, 499.5])),
            id="full-energy-group-resets-values-and-basis",
        ),
        pytest.param(
            dict(zip(ENERGY, [111.0, 222.0, 333.0])),
            {"period_type": "calendar_year", "period_value": 2024},
            {ENERGY[0]: 777.0},
            LATER_BASIS,
            {ENERGY[0]: 111.0},
            {"period_type": "calendar_year", "period_value": 2024},
            {ENERGY[0]: 166.5},
            id="one-present-domestic-no-invented-columns",
        ),
        pytest.param(
            dict(zip(ENERGY, [111.0, 222.0, 333.0])),
            {"period_type": "calendar_year", "period_value": 2024},
            {ENERGY[1]: 888.0},
            LATER_BASIS,
            {ENERGY[1]: 222.0},
            {"period_type": "calendar_year", "period_value": 2024},
            {ENERGY[1]: 333.0},
            id="one-present-electricity-no-invented-columns",
        ),
        pytest.param(
            dict(zip(ENERGY, [111.0, 222.0, 333.0])),
            {"period_type": "calendar_year", "period_value": 2024},
            {ENERGY[2]: 999.0},
            LATER_BASIS,
            {ENERGY[2]: 333.0},
            {"period_type": "calendar_year", "period_value": 2024},
            {ENERGY[2]: 499.5},
            id="one-present-gas-no-invented-columns",
        ),
        pytest.param(
            {ENERGY[0]: 111.0},
            {"period_type": "calendar_year", "period_value": 2026},
            dict(zip(ENERGY, [777.0, 888.0, 999.0])),
            LATER_BASIS,
            dict(zip(ENERGY, [777.0, 888.0, 999.0])),
            LATER_BASIS,
            dict(zip(ENERGY, [932.4, 1065.6, 1198.8])),
            id="same-year-calendar-and-fiscal-bases-remain-distinct",
        ),
        pytest.param(
            {ENERGY[0]: 111.0},
            {"period_type": "calendar_year", "period_value": 2024},
            dict(zip(ENERGY, [777.0, 888.0, 999.0])),
            None,
            dict(zip(ENERGY, [777.0, 888.0, 999.0])),
            None,
            dict(zip(ENERGY, [777.0, 888.0, 999.0])),
            id="labelled-base-unlabelled-later-remains-flat",
        ),
        pytest.param(
            {ENERGY[0]: 111.0},
            None,
            dict(zip(ENERGY, [777.0, 888.0, 999.0])),
            LATER_BASIS,
            dict(zip(ENERGY, [777.0, 888.0, 999.0])),
            LATER_BASIS,
            dict(zip(ENERGY, [932.4, 1065.6, 1198.8])),
            id="unlabelled-base-labelled-later-retains-own-basis",
        ),
        pytest.param(
            {ENERGY[0]: 111.0},
            None,
            dict(zip(ENERGY, [777.0, 888.0, 999.0])),
            None,
            dict(zip(ENERGY, [111.0, 888.0, 999.0])),
            None,
            dict(zip(ENERGY, [111.0, 888.0, 999.0])),
            id="both-unlabelled-overlap-reset-remains-flat",
        ),
        pytest.param(
            dict(zip(ENERGY, [111.0, 222.0, 333.0])),
            {"period_type": "calendar_year", "period_value": 2024},
            {},
            LATER_BASIS,
            {},
            LATER_BASIS,
            None,
            id="no-later-energy-preserves-declaration-and-absence",
        ),
        pytest.param(
            {ENERGY[0]: 111.0, "food_and_non_alcoholic_beverages_consumption": 10.0},
            {"period_type": "calendar_year", "period_value": 2024},
            {
                **dict(zip(ENERGY, [777.0, 888.0, 999.0])),
                "food_and_non_alcoholic_beverages_consumption": 20.0,
            },
            LATER_BASIS,
            {
                **dict(zip(ENERGY, [777.0, 888.0, 999.0])),
                "food_and_non_alcoholic_beverages_consumption": 10.0,
            },
            LATER_BASIS,
            dict(zip(ENERGY, [932.4, 1065.6, 1198.8])),
            id="ordinary-consumption-still-resets-while-energy-is-retained",
        ),
    ],
)
def test_energy_reset_controls_preserve_coherent_public_observations(
    tmp_path,
    controlled_parameters,
    base_amounts,
    base_basis,
    later_amounts,
    later_basis,
    expected_reset,
    expected_basis,
    expected_2027,
):
    source = UKMultiYearDataset(
        datasets=[
            _observation(2024, base_amounts, base_basis),
            _observation(2026, later_amounts, later_basis),
        ]
    )
    original = {
        year: {
            "state": _state(source[year]),
            "tables": [
                table.copy(deep=True)
                for table in (
                    source[year].person,
                    source[year].benunit,
                    source[year].household,
                )
            ],
        }
        for year in source.years
    }

    simulation = Simulation(dataset=source, scenario=no_economic_assumptions)
    child = simulation.dataset[2026]
    assert child is not source[2026]
    path = tmp_path / "controlled-energy-child.h5"
    child.save(path)
    reloaded = UKSingleYearDataset(file_path=path)

    # Check the public observations rather than internal encoded enum buffers.
    for year in source.years:
        assert _state(source[year]) == original[year]["state"]
        for before, after in zip(
            original[year]["tables"],
            (source[year].person, source[year].benunit, source[year].household),
        ):
            pd.testing.assert_frame_equal(before, after, check_dtype=False)

    present_energy = {name for name in expected_reset if name in ENERGY}
    for observation in (child, reloaded):
        assert {
            name for name in ENERGY if name in observation.household
        } == present_energy
        assert observation.energy_price_basis == expected_basis
        for name, amount in expected_reset.items():
            np.testing.assert_array_equal(observation.household[name], [amount])
    for name, amount in expected_reset.items():
        np.testing.assert_array_equal(simulation.calculate(name, 2026), [amount])

    # Empty energy groups have no asserted projection-metadata contract here.
    if expected_2027 is not None:
        extended = extend_single_year_dataset(
            reloaded, controlled_parameters, end_year=2027
        )[2027]
        assert {name for name in ENERGY if name in extended.household} == present_energy
        for name, amount in expected_2027.items():
            np.testing.assert_allclose(extended.household[name], [amount])
        assert extended.energy_price_basis == (
            {"period_type": "fiscal_year", "period_value": 2027}
            if expected_basis is not None
            else None
        )

    # Calculation and re-extension must also leave the caller's tables intact.
    for year in source.years:
        assert _state(source[year]) == original[year]["state"]
        for before, after in zip(
            original[year]["tables"],
            (source[year].person, source[year].benunit, source[year].household),
        ):
            pd.testing.assert_frame_equal(before, after, check_dtype=False)
