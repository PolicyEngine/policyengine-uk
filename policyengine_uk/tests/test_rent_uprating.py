from types import SimpleNamespace

import pandas as pd
import pytest

from policyengine_uk import parameters
from policyengine_uk.data.economic_assumptions import uprate_rent


PRIVATE_RENTAL_HOUSEHOLDS = 0.188
SOCIAL_RENTAL_HOUSEHOLDS = 0.164
PRIVATE_RENT_WEIGHT = PRIVATE_RENTAL_HOUSEHOLDS / (
    PRIVATE_RENTAL_HOUSEHOLDS + SOCIAL_RENTAL_HOUSEHOLDS
)
SOCIAL_RENT_WEIGHT = SOCIAL_RENTAL_HOUSEHOLDS / (
    PRIVATE_RENTAL_HOUSEHOLDS + SOCIAL_RENTAL_HOUSEHOLDS
)


def test_uprate_rent_uses_tenure_specific_growth():
    previous_year = SimpleNamespace(
        household=pd.DataFrame({"rent": [1_000.0, 1_000.0]})
    )
    current_year = SimpleNamespace(
        time_period="2025",
        household=pd.DataFrame(
            {
                "tenure_type": ["RENT_PRIVATELY", "RENT_FROM_COUNCIL"],
                "region": ["LONDON", "LONDON"],
                "rent": [0.0, 0.0],
            }
        ),
    )

    uprate_rent(current_year, previous_year, parameters)

    assert current_year.household["rent"][0] == pytest.approx(1_066.484)
    assert current_year.household["rent"][1] == pytest.approx(1_080.0)


def test_forecast_private_rent_preserves_obr_aggregate_growth():
    growth = parameters.gov.economic_assumptions.yoy_growth

    for year in range(2026, 2031):
        private_rent_growth = growth.ons.private_rental_prices(year)["UNITED_KINGDOM"]
        social_rent_growth = growth.obr.social_rent(year)
        aggregate_rent_growth = growth.obr.rent(year)

        weighted_growth = (
            PRIVATE_RENT_WEIGHT * private_rent_growth
            + SOCIAL_RENT_WEIGHT * social_rent_growth
        )
        assert weighted_growth == pytest.approx(aggregate_rent_growth)
