"""Residential stocks and HVCTS use one annual house-price basis (#2392).

These are synthetic households. Factors below use the model's existing
March 2026 OBR annual HPI assumptions, not a month-specific observation.
The surcharge's published 2026 valuation bands supply the charge oracle.
"""

import numpy as np
import pandas as pd
import pytest

from policyengine_uk import Microsimulation, Simulation
from policyengine_uk.data import UKSingleYearDataset
from policyengine_uk.data.economic_assumptions import (
    extend_single_year_dataset,
    uprating_input_fingerprint,
)
from policyengine_uk.model_api import Scenario
from policyengine_uk.scenarios import no_economic_assumptions

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")
ASSETS = ["main_residence_value", "other_residential_property_value"]
HPI_2026_TO_2028 = 1.029 * 1.027
MAIN_VALUES = np.array([1_880_000, 2_360_000, 3_280_000, 4_700_000], dtype=float)
OTHER_VALUES = np.array([125_000, 0, 900_000, 60_000], dtype=float)


def property_dataset(
    main_values=MAIN_VALUES, other_values=OTHER_VALUES, fiscal_year=2024
):
    """One adult per synthetic owner household, with no private data."""
    ids = np.arange(1, len(main_values) + 1)
    return UKSingleYearDataset(
        person=pd.DataFrame(
            {
                "person_id": ids,
                "person_benunit_id": ids,
                "person_household_id": ids,
                "age": 40,
                "employment_income": 0.0,
            }
        ),
        benunit=pd.DataFrame({"benunit_id": ids}),
        household=pd.DataFrame(
            {
                "household_id": ids,
                "household_weight": 1.0,
                "region": "LONDON",
                "tenure_type": "OWNED_OUTRIGHT",
                "rent": 0.0,
                "council_tax": 0.0,
                "main_residence_value": main_values,
                "other_residential_property_value": other_values,
            }
        ),
        fiscal_year=fiscal_year,
    )


@pytest.fixture(scope="module")
def projected_properties(cloned_uk_tax_benefit_system):
    return Microsimulation(dataset=property_dataset())


@pytest.mark.parametrize("asset", ASSETS)
def test_direct_property_stock_uses_house_price_growth(asset):
    sim = Simulation(
        situation={
            "people": {"adult": {"age": {2024: 40}}},
            "households": {"home": {"members": ["adult"], asset: {2024: 1_880_000}}},
        }
    )
    # Core carries inputs with cumulative index levels, which the model
    # rounds to five decimal places. Select the required HPI explicitly;
    # dataset stocks need that same cumulative price basis.
    hpi = sim.tax_benefit_system.parameters.get_child(
        "gov.economic_assumptions.indices.obr.house_prices"
    )
    for year in [2024, 2026, 2028]:
        assert sim.calculate(asset, year)[0] == pytest.approx(
            1_880_000 * hpi(year) / hpi(2024), abs=0.25
        )


@pytest.mark.parametrize("asset,values", zip(ASSETS, [MAIN_VALUES, OTHER_VALUES]))
def test_dataset_property_stocks_use_house_price_growth(
    projected_properties, asset, values
):
    hpi = projected_properties.tax_benefit_system.parameters.get_child(
        "gov.economic_assumptions.indices.obr.house_prices"
    )
    for year in [2024, 2026, 2028]:
        factor = hpi(year) / hpi(2024)
        # Match Core's input storage type before the single ratio is applied.
        expected = values.astype(np.float32) * factor
        # Stored dataset arrays take precedence over Core's variable-level
        # uprating, so both paths need the same house-price series.
        np.testing.assert_allclose(
            projected_properties.dataset[year].household[asset], expected
        )
        np.testing.assert_allclose(
            projected_properties.calculate(asset, year), expected, atol=0.25
        )


def test_projected_homes_use_2026_house_price_bands(projected_properties):
    # HPI places these 2024 homes just below each 2026 band boundary.
    # GDP-per-capita growth places all four above the respective boundary.
    np.testing.assert_array_equal(
        projected_properties.calculate("high_value_council_tax_surcharge", 2028),
        [0, 2_500, 3_500, 5_000],
    )


def test_later_bill_preserves_a_supplied_2026_property_value():
    sim = Simulation(
        situation={
            "people": {"adult": {"age": {2026: 40}}},
            "households": {
                "home": {
                    "members": ["adult"],
                    "region": "LONDON",
                    "tenure_type": "OWNED_OUTRIGHT",
                    "main_residence_value": {2026: 2_010_000},
                }
            },
        }
    )
    assert sim.calculate("high_value_council_tax_surcharge", 2028)[0] == 2_500


def test_house_price_valuation_reaches_final_tax_totals():
    # Supply a 2028 value corresponding to £2.01m on the annual 2026 basis.
    # The old GDP reversal instead puts it below £2m and charges nothing.
    situation = {
        "people": {"adult": {"age": {2028: 40}, "employment_income": 0}},
        "households": {
            "home": {
                "members": ["adult"],
                "region": "LONDON",
                "tenure_type": "OWNED_OUTRIGHT",
                "main_residence_value": {2028: 2_010_000 * HPI_2026_TO_2028},
                "council_tax": 0,
                "household_owns_tv": False,
                "property_purchased": False,
            }
        },
    }
    sim = Simulation(
        situation=situation,
        scenario=Scenario(
            parameter_changes={"gov.contrib.abolish_council_tax": {"2028": True}}
        ),
    )
    assert sim.baseline.calculate("high_value_council_tax_surcharge", 2028)[0] == 2_500
    # The abolition removes this charge from the tax aggregates. Compare the
    # difference so unrelated existing transaction-tax heads are not forced
    # to zero or mistaken for surcharge revenue.
    for variable in ["household_tax", "gov_tax"]:
        np.testing.assert_allclose(
            sim.baseline.calculate(variable, 2028) - sim.calculate(variable, 2028),
            [2_500],
        )


@pytest.mark.parametrize("source", ["dataset", "direct"])
def test_projection_preserves_supplied_2026_band_boundaries(source):
    # Official 2026 valuation bands, at each threshold and £1 below it.
    # Forward projection alone must not move a 2026 observation to another
    # 2026 band when the surcharge converts it back from the simulated year.
    values = np.array(
        [
            1_999_999,
            2_000_000,
            2_499_999,
            2_500_000,
            3_499_999,
            3_500_000,
            4_999_999,
            5_000_000,
        ],
        dtype=float,
    )
    if source == "dataset":
        sim = Microsimulation(
            dataset=property_dataset(values, np.zeros(len(values)), fiscal_year=2026)
        )
    else:
        people = {f"adult{i}": {"age": {2026: 40}} for i in range(len(values))}
        homes = {
            f"home{i}": {
                "members": [f"adult{i}"],
                "region": "LONDON",
                "tenure_type": "OWNED_OUTRIGHT",
                "main_residence_value": {2026: float(value)},
            }
            for i, value in enumerate(values)
        }
        sim = Simulation(situation={"people": people, "households": homes})
    np.testing.assert_array_equal(
        sim.calculate("high_value_council_tax_surcharge", 2028),
        [0, 2_500, 2_500, 3_500, 3_500, 5_000, 5_000, 7_500],
    )


def test_projection_fingerprints_cumulative_house_price_overrides(projected_properties):
    # The dataset cache key must cover the effective cumulative index now
    # read by residential projection, even if the raw YoY series is unchanged.
    parameters = projected_properties.tax_benefit_system.parameters.clone()
    baseline = uprating_input_fingerprint(parameters)
    hpi = parameters.get_child("gov.economic_assumptions.indices.obr.house_prices")
    changed_level = hpi(2027) * 1.1
    hpi.update(period="2027", value=changed_level)
    assert uprating_input_fingerprint(parameters) != baseline
    projected = extend_single_year_dataset(
        property_dataset(fiscal_year=2026), parameters, end_year=2027
    )
    factor = changed_level / hpi(2026)
    for asset, values in zip(ASSETS, [MAIN_VALUES, OTHER_VALUES]):
        np.testing.assert_allclose(projected[2027].household[asset], values * factor)


def test_frozen_assumptions_keep_residential_stocks_at_observed_values():
    sim = Microsimulation(dataset=property_dataset(), scenario=no_economic_assumptions)
    for asset, values in zip(ASSETS, [MAIN_VALUES, OTHER_VALUES]):
        np.testing.assert_array_equal(sim.calculate(asset, 2028), values)
