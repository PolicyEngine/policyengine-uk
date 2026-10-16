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
from policyengine_uk.model_api import Scenario

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")
ASSETS = ["main_residence_value", "other_residential_property_value"]
HPI_2024_TO_2026 = 1.028 * 1.024
HPI_2026_TO_2028 = 1.029 * 1.027
MAIN_VALUES = np.array([1_880_000, 2_360_000, 3_280_000, 4_700_000], dtype=float)
OTHER_VALUES = np.array([125_000, 0, 900_000, 60_000], dtype=float)


def property_dataset():
    """One adult in each of four owner households, with no private data."""
    ids = np.arange(1, 5)
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
                "main_residence_value": MAIN_VALUES,
                "other_residential_property_value": OTHER_VALUES,
            }
        ),
        fiscal_year=2024,
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
    # the dataset test independently checks the unrounded YoY arithmetic.
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
    for year, factor in [
        (2024, 1),
        (2026, HPI_2024_TO_2026),
        (2028, HPI_2024_TO_2026 * HPI_2026_TO_2028),
    ]:
        # Stored dataset arrays take precedence over Core's variable-level
        # uprating, so both paths need the same house-price series.
        np.testing.assert_allclose(
            projected_properties.dataset[year].household[asset], values * factor
        )
        np.testing.assert_allclose(
            projected_properties.calculate(asset, year), values * factor, atol=0.25
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
