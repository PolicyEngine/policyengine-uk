import pandas as pd
import pytest

from policyengine_uk.data.dataset_schema import UKSingleYearDataset
from policyengine_uk.data.economic_assumptions import extend_single_year_dataset
from policyengine_uk.system import system


def test_petrol_and_diesel_spending_use_road_fuel_volume_not_cpi():
    parameters = system.parameters
    road_fuel_volume = (
        parameters.gov.economic_assumptions.yoy_growth.obr.road_fuel_volume
    )
    cpi = parameters.gov.economic_assumptions.yoy_growth.obr.consumer_price_index

    assert road_fuel_volume(2027) < 0
    assert cpi(2027) > 0

    dataset = UKSingleYearDataset(
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
                "council_tax": [1_500.0],
                "rent": [0.0],
                "petrol_spending": [1_000.0],
                "diesel_spending": [2_000.0],
            }
        ),
        fiscal_year=2026,
    )

    extended = extend_single_year_dataset(
        dataset,
        tax_benefit_system_parameters=parameters,
        end_year=2027,
    )
    household_2027 = extended[2027].household

    assert household_2027["petrol_spending"].iloc[0] == pytest.approx(
        1_000 * (1 + road_fuel_volume(2027))
    )
    assert household_2027["diesel_spending"].iloc[0] == pytest.approx(
        2_000 * (1 + road_fuel_volume(2027))
    )
    assert household_2027["petrol_spending"].iloc[0] < 1_000
    assert household_2027["diesel_spending"].iloc[0] < 2_000
