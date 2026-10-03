import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from policyengine_uk import Microsimulation, parameters
from policyengine_uk.data import UKSingleYearDataset
from policyengine_uk.data.economic_assumptions import extend_single_year_dataset
from policyengine_uk.scenarios import no_economic_assumptions
from policyengine_uk.variables.household.demographic.geography import Region

DOMESTIC_RATES_GROWTH = (
    parameters.gov.economic_assumptions.yoy_growth.finance_ni.domestic_rates
)
DOMESTIC_RATES_INDEX = (
    parameters.gov.economic_assumptions.indices.finance_ni.domestic_rates
)

# Published inputs to the growth series, keyed by the first calendar year of
# each fiscal year (2026 = 2026-27). Domestic poundages are £ per £ of capital
# value, from the Department of Finance rate poundages tables (current page and
# its 6 July 2023 archive). Domestic rates paid are LPS's "Domestic Rates
# collected by District Council", 2020-21 to 2025-26.
REGIONAL_RATE = {
    2019: 0.004574,
    2020: 0.004574,
    2021: 0.004574,
    2022: 0.004574,
    2023: 0.004848,
    2024: 0.005042,
    2025: 0.005294,
    2026: 0.005559,
}
POUNDAGE_YEARS = list(REGIONAL_RATE)
DISTRICT_RATES = {
    "Antrim and Newtownabbey": (0.003578, 0.003649, 0.003649, 0.003718, 0.0039, 0.004094, 0.004297, 0.004425),
    "Ards and North Down": (0.003262, 0.003446, 0.003521, 0.003618, 0.003864, 0.004095, 0.004244, 0.004435),
    "Armagh City, Banbridge and Craigavon": (0.004312, 0.004419, 0.004507, 0.004596, 0.004818, 0.005067, 0.005265, 0.005412),
    "Belfast": (0.003327, 0.003394, 0.003459, 0.003562, 0.003847, 0.004056, 0.004299, 0.004492),
    "Causeway Coast and Glens": (0.003621, 0.003892, 0.003989, 0.004128, 0.004457, 0.004762, 0.004936, 0.005101),
    "Derry City and Strabane": (0.004845, 0.005009, 0.005103, 0.005279, 0.0057, 0.00607, 0.006369, 0.006655),
    "Fermanagh and Omagh": (0.003568, 0.003668, 0.003718, 0.003819, 0.004033, 0.004223, 0.004382, 0.004468),
    "Lisburn and Castlereagh": (0.003037, 0.003158, 0.003158, 0.003273, 0.003518, 0.003658, 0.003804, 0.003966),
    "Mid and East Antrim": (0.004296, 0.004371, 0.004414, 0.004575, 0.004823, 0.005295, 0.005506, 0.005668),
    "Mid Ulster": (0.003267, 0.003373, 0.003373, 0.003505, 0.003761, 0.003983, 0.004188, 0.00433),
    "Newry, Mourne and Down": (0.003893, 0.004004, 0.004067, 0.004146, 0.004395, 0.004676, 0.004862, 0.004999),
}  # fmt: skip
PAID_FROM = 2020  # first fiscal year in DOMESTIC_RATES_PAID
DOMESTIC_RATES_PAID = {
    "Antrim and Newtownabbey": (51877954, 53609226, 54941178, 59598012, 62740303, 67083237),
    "Ards and North Down": (77169538, 80000514, 81880418, 88782827, 93831109, 99315112),
    "Armagh City, Banbridge and Craigavon": (77677974, 81263782, 84022142, 90651436, 96143969, 102310045),
    "Belfast": (128450302, 132243016, 135252391, 146695586, 154922721, 164710647),
    "Causeway Coast and Glens": (59783287, 62302754, 64057127, 70213526, 74638296, 79507631),
    "Derry City and Strabane": (50504688, 52578700, 54546640, 59502890, 63416021, 67761117),
    "Fermanagh and Omagh": (40044670, 41887670, 43196251, 46923175, 49869460, 52744966),
    "Lisburn and Castlereagh": (63085716, 64919429, 67279724, 73375284, 77271131, 82506955),
    "Mid and East Antrim": (54583730, 56532538, 58556508, 62884156, 68012052, 72388680),
    "Mid Ulster": (47848174, 49979975, 51804985, 57194629, 61101622, 65497725),
    "Newry, Mourne and Down": (69820431, 73012766, 75606011, 82112996, 87596475, 94062463),
}  # fmt: skip


def _bill_growth(year):
    # Growth in the combined (regional plus district) domestic poundage,
    # weighting each council by its domestic rates paid the year before.
    # 2019-20 payments are not published, so 2020-21's stand in.
    weight_year = max(year - 1, PAID_FROM)
    growth = 0.0
    total_weight = 0.0
    for council, district in DISTRICT_RATES.items():
        weight = DOMESTIC_RATES_PAID[council][weight_year - PAID_FROM]
        now = district[POUNDAGE_YEARS.index(year)] + REGIONAL_RATE[year]
        before = district[POUNDAGE_YEARS.index(year - 1)] + REGIONAL_RATE[year - 1]
        growth += weight * now / before
        total_weight += weight
    return growth / total_weight - 1


# The checked years follow the tables, so a refresh only adds a year's data.
LAST_PUBLISHED_YEAR = POUNDAGE_YEARS[-1]


@pytest.mark.parametrize("year", POUNDAGE_YEARS[1:])
def test_domestic_rates_growth_matches_published_poundages(year):
    assert DOMESTIC_RATES_GROWTH(year) == round(_bill_growth(year), 4)


@pytest.mark.parametrize("year", range(LAST_PUBLISHED_YEAR + 1, 2031))
def test_domestic_rates_growth_holds_last_published_growth(year):
    assert DOMESTIC_RATES_GROWTH(year) == DOMESTIC_RATES_GROWTH(LAST_PUBLISHED_YEAR)


# A dataset with an unknown-region household cannot be projected forward until
# rent uprating handles Region.UNKNOWN (#1985), so the tests use the twelve
# known regions.
KNOWN_REGIONS = [region.name for region in Region if region.name != "UNKNOWN"]


def _dataset(regions, domestic_rates, base_year=2023):
    ids = np.arange(1, len(regions) + 1)
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
                "region": regions,
                "tenure_type": "OWNED_OUTRIGHT",
                "rent": 0.0,
                "council_tax": 0.0,
                "domestic_rates": domestic_rates,
            }
        ),
        fiscal_year=base_year,
    )


def _northern_ireland_only(amount):
    return _dataset(
        KNOWN_REGIONS,
        [amount if region == "NORTHERN_IRELAND" else 0.0 for region in KNOWN_REGIONS],
    )


def _compounded(amount, year, base_year=2023):
    return amount * np.prod(
        [1 + DOMESTIC_RATES_GROWTH(y) for y in range(base_year + 1, year + 1)]
    )


def test_extended_dataset_uprates_northern_ireland_domestic_rates():
    # Before #1990 every projected year kept the base year's bill.
    extended = extend_single_year_dataset(
        _northern_ireland_only(1_000.0), parameters, end_year=2030
    )
    northern_ireland = KNOWN_REGIONS.index("NORTHERN_IRELAND")

    for year in range(2024, 2031):
        domestic_rates = extended[year].household["domestic_rates"].to_numpy()
        assert domestic_rates[northern_ireland] == pytest.approx(
            _compounded(1_000.0, year)
        )
        assert np.delete(domestic_rates, northern_ireland).sum() == 0
    assert extended[2024].household["domestic_rates"].iloc[
        northern_ireland
    ] == pytest.approx(1_049.1)
    assert extended[2026].household["domestic_rates"].iloc[
        northern_ireland
    ] == pytest.approx(1_000 * 1.0491 * 1.0474 * 1.0433)


def test_microsimulation_uprates_northern_ireland_domestic_rates():
    sim = Microsimulation(dataset=_northern_ireland_only(1_000.0))

    for year in (2026, 2030):
        domestic_rates = dict(
            zip(KNOWN_REGIONS, sim.calculate("domestic_rates", year).values)
        )
        assert domestic_rates["NORTHERN_IRELAND"] == pytest.approx(
            _compounded(1_000.0, year)
        )
        assert domestic_rates["LONDON"] == 0


def test_no_economic_assumptions_holds_domestic_rates_flat():
    sim = Microsimulation(
        dataset=_northern_ireland_only(1_000.0), scenario=no_economic_assumptions
    )

    domestic_rates = dict(
        zip(KNOWN_REGIONS, sim.calculate("domestic_rates", 2030).values)
    )
    assert domestic_rates["NORTHERN_IRELAND"] == pytest.approx(1_000.0)


@settings(max_examples=40, deadline=None, derandomize=True)
@given(
    households=st.lists(
        st.tuples(
            st.sampled_from(KNOWN_REGIONS),
            st.floats(0, 10_000, allow_nan=False),
        ),
        min_size=1,
        max_size=12,
    ),
    base_year=st.integers(2022, 2029),
    scale=st.floats(0, 10, allow_nan=False),
)
def test_domestic_rates_projection_properties(households, base_year, scale):
    """For any domestic rates of zero or more, any region and any base year:

    - each year's bill is the base bill times the product of the growth
      factors since the base year;
    - that product equals the ratio of the cumulative index the model builds
      from the same growth series (a second path, rounded to 5 decimals);
    - every household's bill grows by the same factor, whatever its region,
      so each result depends only on its own row;
    - scaling every base bill scales every projected bill by the same factor;
    - no projected bill falls below the base bill.
    """
    regions, amounts = (list(column) for column in zip(*households))
    amounts = np.array(amounts)
    end_year = 2030

    projected = extend_single_year_dataset(
        _dataset(regions, amounts, base_year), parameters, end_year=end_year
    )
    scaled = extend_single_year_dataset(
        _dataset(regions, scale * amounts, base_year), parameters, end_year=end_year
    )

    for year in range(base_year + 1, end_year + 1):
        factor = np.prod(
            [1 + DOMESTIC_RATES_GROWTH(y) for y in range(base_year + 1, year + 1)]
        )
        assert factor == pytest.approx(
            DOMESTIC_RATES_INDEX(year) / DOMESTIC_RATES_INDEX(base_year), rel=1e-4
        )
        domestic_rates = projected[year].household["domestic_rates"].to_numpy()
        assert domestic_rates == pytest.approx(amounts * factor)
        assert (domestic_rates >= amounts).all()
        assert scaled[year].household["domestic_rates"].to_numpy() == pytest.approx(
            scale * domestic_rates
        )
