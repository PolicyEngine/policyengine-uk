"""Water and sewerage charges are projected by each country's own path.

Ofwat's average bill series covers England and Wales. Scottish Water sets
Scotland's charges under limits from the Water Industry Commission for
Scotland, and Northern Ireland has no domestic water charges
(PolicyEngine/policyengine-uk#2501).
"""

from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from policyengine_uk import Microsimulation, parameters
from policyengine_uk.data import UKSingleYearDataset
from policyengine_uk.data.economic_assumptions import (
    extend_single_year_dataset,
    reset_growthfactor_uprating,
    uprate_water_charges,
    uprating_input_paths,
)
from policyengine_uk.variables.household.demographic.geography import Region

OFWAT = parameters.gov.economic_assumptions.yoy_growth.ofwat.water_bills
SCOTTISH_WATER_PATH = "gov.economic_assumptions.yoy_growth.scottish_water.water_bills"
# One household per known region. Region.UNKNOWN is left out of the
# dataset-level tests because rent uprating cannot project it yet (#1985).
KNOWN_REGIONS = [region.name for region in Region if region.name != "UNKNOWN"]
BASE_YEAR = 2024


def _dataset(water=400.0):
    ids = np.arange(1, len(KNOWN_REGIONS) + 1)
    return UKSingleYearDataset(
        person=pd.DataFrame(
            {
                "person_id": ids,
                "person_benunit_id": ids,
                "person_household_id": ids,
                "age": 40,
            }
        ),
        benunit=pd.DataFrame({"benunit_id": ids}),
        household=pd.DataFrame(
            {
                "household_id": ids,
                "household_weight": 1.0,
                "region": KNOWN_REGIONS,
                "tenure_type": "OWNED_OUTRIGHT",
                "rent": 0.0,
                "council_tax": 0.0,
                "water_and_sewerage_charges": water,
            }
        ),
        fiscal_year=BASE_YEAR,
    )


def _water(dataset, region):
    household = dataset.household
    return household["water_and_sewerage_charges"][household["region"] == region].iloc[
        0
    ]


@pytest.fixture(scope="module")
def projected():
    return extend_single_year_dataset(_dataset(), parameters)


def test_scottish_charges_follow_scottish_water_published_rises(projected):
    # Scottish Water: +9.9% from 1 April 2025, +8.67% from 1 April 2026.
    # 400 x 1.099 = 439.60; 439.60 x 1.0867 = 477.71332.
    assert _water(projected[2025], "SCOTLAND") == pytest.approx(439.60)
    assert _water(projected[2026], "SCOTLAND") == pytest.approx(477.71332)


def test_scottish_charges_assume_cpi_plus_two_per_cent_from_2027(projected):
    # WICS draft determination cap CPI + 2%, with OBR CPI at 2.0%: 4% a year.
    # 477.71332 x 1.04 = 496.8218528; x 1.04 again = 516.69472691.
    assert _water(projected[2027], "SCOTLAND") == pytest.approx(496.8218528)
    assert _water(projected[2028], "SCOTLAND") == pytest.approx(516.69472691)
    for year in (2031, 2032):
        assert _water(projected[year], "SCOTLAND") == pytest.approx(
            _water(projected[year - 1], "SCOTLAND") * 1.04
        )


def test_england_and_wales_charges_follow_ofwat(projected):
    for region in ("LONDON", "NORTH_EAST", "WALES"):
        expected = 400.0
        for year in range(BASE_YEAR + 1, 2033):
            expected *= 1 + OFWAT(year)
            assert _water(projected[year], region) == pytest.approx(expected), (
                region,
                year,
            )


def test_northern_ireland_charges_are_held_flat(projected):
    # Northern Ireland has no domestic water charges, so a charge a dataset
    # gives a household there is not grown by the England and Wales rate.
    for year in range(BASE_YEAR + 1, 2033):
        assert _water(projected[year], "NORTHERN_IRELAND") == 400.0


def test_microsimulation_uses_the_scottish_path():
    sim = Microsimulation(dataset=_dataset())
    water = dict(
        zip(KNOWN_REGIONS, sim.calculate("water_and_sewerage_charges", 2026).values)
    )
    assert water["SCOTLAND"] == pytest.approx(477.71332)
    assert water["NORTHERN_IRELAND"] == 400.0
    assert water["LONDON"] == pytest.approx(
        400.0 * (1 + OFWAT(2025)) * (1 + OFWAT(2026))
    )


def _uprated(regions, water, year):
    previous_year = SimpleNamespace(
        household=pd.DataFrame({"water_and_sewerage_charges": water}, dtype=float)
    )
    current_year = SimpleNamespace(
        time_period=str(year),
        household=pd.DataFrame(
            {"region": regions, "water_and_sewerage_charges": [0.0] * len(water)}
        ),
    )
    uprate_water_charges(current_year, previous_year, parameters)
    return current_year.household["water_and_sewerage_charges"].to_numpy()


def test_unknown_region_takes_ofwat_growth():
    assert _uprated(["UNKNOWN"], [400.0], 2025) == pytest.approx(
        [400.0 * (1 + OFWAT(2025))]
    )


@pytest.mark.parametrize("region", ["NORTHERN IRELAND", "ATLANTIS", ""])
def test_unrecognised_regions_are_rejected(region):
    with pytest.raises(ValueError, match="unrecognised regions"):
        _uprated(["LONDON", region], [400.0, 400.0], 2025)


def test_scottish_series_is_part_of_the_uprating_fingerprint():
    assert SCOTTISH_WATER_PATH in uprating_input_paths()


def test_reset_growthfactor_uprating_restores_water_charges(projected):
    reset = reset_growthfactor_uprating(projected.copy())
    for year in range(BASE_YEAR + 1, 2033):
        np.testing.assert_array_equal(
            reset[year].household["water_and_sewerage_charges"].to_numpy(),
            np.full(len(KNOWN_REGIONS), 400.0),
        )
