from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from policyengine_core.errors import ParameterNotFoundError

from policyengine_uk import Microsimulation, parameters
from policyengine_uk.data import UKSingleYearDataset
from policyengine_uk.data.economic_assumptions import uprate_rent
from policyengine_uk.variables.household.demographic.geography import Region


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


REGIONS = [region.name for region in Region]
TENURES = ["RENT_PRIVATELY", "RENT_FROM_COUNCIL", "RENT_FROM_HA", "OWNED_OUTRIGHT"]
UPRATED_YEARS = list(range(2022, 2031))


def _uprated_rent(regions, tenures, rents, year):
    previous_year = SimpleNamespace(household=pd.DataFrame({"rent": rents}))
    current_year = SimpleNamespace(
        time_period=str(year),
        household=pd.DataFrame(
            {"tenure_type": tenures, "region": regions, "rent": [0.0] * len(rents)}
        ),
    )
    uprate_rent(current_year, previous_year, parameters)
    return current_year.household["rent"].to_numpy()


def test_uprate_rent_gives_unknown_region_the_uk_index():
    # Region.UNKNOWN is a valid region (for example SPI records with an
    # address abroad) but has no rent index of its own. It used to raise
    # ParameterNotFoundError, so no such dataset could be simulated.
    rent = _uprated_rent(
        ["UNKNOWN", "UNKNOWN"],
        ["RENT_PRIVATELY", "RENT_FROM_COUNCIL"],
        [1_000.0] * 2,
        2025,
    )

    assert rent[0] == pytest.approx(1_063.279)
    assert rent[1] == pytest.approx(1_080.0)


def test_uprate_rent_still_rejects_unrecognised_regions():
    with pytest.raises(ParameterNotFoundError):
        _uprated_rent(["ATLANTIS"], ["RENT_PRIVATELY"], [1_000.0], 2025)


@settings(max_examples=100, deadline=None, derandomize=True)
@given(
    households=st.lists(
        st.tuples(
            st.sampled_from(REGIONS),
            st.sampled_from(TENURES),
            st.floats(0, 100_000, allow_nan=False),
        ),
        min_size=1,
        max_size=30,
    ),
    year=st.sampled_from(UPRATED_YEARS),
)
def test_uprate_rent_properties(households, year):
    """For every region in the Region enum, any tenure and any rent:

    - a private rent grows by its region's index, read one region at a time
      (a second path to the same numbers as the vectorised lookup), and by
      the UK-wide index where the region is unknown;
    - any other rent grows by the social rent index, whatever the region;
    - each household's result depends only on its own row.
    """
    regions, tenures, rents = (list(column) for column in zip(*households))
    growth = parameters.gov.economic_assumptions.yoy_growth
    private = growth.ons.private_rental_prices(year)
    social = growth.obr.social_rent(year)

    expected = [
        rent
        * (
            1
            + (
                social
                if tenure != "RENT_PRIVATELY"
                else private["UNITED_KINGDOM" if region == "UNKNOWN" else region]
            )
        )
        for region, tenure, rent in households
    ]

    rent = _uprated_rent(regions, tenures, rents, year)

    assert rent == pytest.approx(expected)
    alone = [
        _uprated_rent([region], [tenure], [value], year)[0]
        for region, tenure, value in households
    ]
    assert rent == pytest.approx(alone)


def _spi_shaped_dataset(regions, scottish_taxpayer=None):
    # One person per benefit unit and household, as in the Survey of Personal
    # Incomes, where a record carries no household information.
    ids = np.arange(1, len(regions) + 1)
    person = pd.DataFrame(
        {
            "person_id": ids,
            "person_benunit_id": ids,
            "person_household_id": ids,
            "age": 40,
            "employment_income": 60_000.0,
        }
    )
    if scottish_taxpayer is not None:
        person["pays_scottish_income_tax"] = scottish_taxpayer
    household = pd.DataFrame(
        {
            "household_id": ids,
            "household_weight": 1.0,
            "region": regions,
            "rent": 0.0,
            "tenure_type": "OWNED_OUTRIGHT",
            "council_tax": 0.0,
        }
    )
    return UKSingleYearDataset(
        person=person,
        benunit=pd.DataFrame({"benunit_id": ids}),
        household=household,
        fiscal_year=2022,
    )


def test_microsimulation_runs_on_dataset_with_unknown_region():
    sim = Microsimulation(
        dataset=_spi_shaped_dataset(["UNKNOWN", "LONDON", "SCOTLAND"])
    )

    for year in (2022, 2030):
        unknown, london, scotland = sim.calculate("income_tax", year).values
        assert unknown > 0
        # An unknown region is not Scotland, so the rest-of-UK rates apply.
        assert unknown == london
        assert scotland != london


def test_scottish_taxpayer_flag_overrides_unknown_region():
    # A dataset can say who pays Scottish rates directly (the SPI's SCOT_TXP)
    # where the region cannot.
    sim = Microsimulation(
        dataset=_spi_shaped_dataset(
            ["UNKNOWN", "UNKNOWN", "SCOTLAND"], scottish_taxpayer=[True, False, True]
        )
    )

    flagged, unflagged, scotland = sim.calculate("income_tax", 2022).values
    assert flagged == scotland
    assert flagged != unflagged
