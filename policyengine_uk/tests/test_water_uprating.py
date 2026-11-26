"""Dataset projection uprates water and sewerage charges by country (#2501).

Ofwat's series is the average household bill in England and Wales. Scottish
Water's charges are set separately, within limits from the Water Industry
Commission for Scotland, and rose 9.9% in 2025-26 against Ofwat's 26%.
Northern Ireland has no domestic water charges, so any a dataset gives its
households are held flat.
"""

import functools
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from policyengine_uk import Microsimulation, Simulation, parameters
from policyengine_uk.data import UKSingleYearDataset
from policyengine_uk.data.economic_assumptions import (
    LEGACY_PROJECTION_END_YEAR,
    PROJECTION_END_YEAR,
    _unmapped_uprating_indices,
    _uprating_index_map,
    extend_single_year_dataset,
    uprate_water_and_sewerage_charges,
    uprating_input_paths,
)
from policyengine_uk.variables.household.demographic.geography import Region


REGIONS = [region.name for region in Region]
UPRATED_YEARS = list(range(2023, PROJECTION_END_YEAR + 1))
GROWTH = parameters.gov.economic_assumptions.yoy_growth
ENGLAND_AND_WALES = GROWTH.ofwat.water_bills
SCOTLAND = GROWTH.scottish_water.water_bills


@functools.cache
def _country_of_each_region():
    # The model's own region-to-country mapping (the `country` variable), a
    # second path to the one the uprating code takes.
    people = {f"person_{region}": {"age": 40} for region in REGIONS}
    households = {
        f"household_{region}": {"members": [f"person_{region}"], "region": region}
        for region in REGIONS
    }
    sim = Simulation(situation={"people": people, "households": households})
    countries = sim.calculate("country", 2025)
    return dict(zip(REGIONS, countries))


@pytest.fixture(scope="module", autouse=True)
def release_region_mapping():
    # Drop the cached mapping once this module's tests are done, instead of
    # keeping it for the rest of the test process.
    yield
    _country_of_each_region.cache_clear()


def _expected_growth(region, year):
    country = _country_of_each_region()[region]
    if country == "NORTHERN_IRELAND":
        return 0.0
    if country == "SCOTLAND":
        return SCOTLAND(year)
    # England, Wales and an unknown region take the England and Wales bills.
    return ENGLAND_AND_WALES(year)


def _uprated(regions, charges, year):
    previous_year = SimpleNamespace(
        household=pd.DataFrame({"water_and_sewerage_charges": charges}, dtype=float)
    )
    current_year = SimpleNamespace(
        time_period=str(year),
        household=pd.DataFrame(
            {"region": regions, "water_and_sewerage_charges": [0.0] * len(charges)}
        ),
    )
    uprate_water_and_sewerage_charges(current_year, previous_year, parameters)
    return current_year.household["water_and_sewerage_charges"].to_numpy()


def test_scottish_water_growth_matches_its_sources():
    # Scottish Water's announced increases (8.8% approved by WICS on 30
    # January 2024; 9.9% on 28 January 2025; 8.67% on 22 January 2026).
    assert SCOTLAND("2024-01-01") == pytest.approx(0.088)
    assert SCOTLAND("2025-01-01") == pytest.approx(0.099)
    assert SCOTLAND("2026-01-01") == pytest.approx(0.0867)


def test_each_country_takes_its_own_water_growth():
    charges = _uprated(
        ["LONDON", "WALES", "SCOTLAND", "NORTHERN_IRELAND", "UNKNOWN"],
        [500.0] * 5,
        2025,
    )
    england_and_wales = 500 * (1 + ENGLAND_AND_WALES("2025-01-01"))
    assert charges == pytest.approx(
        [england_and_wales, england_and_wales, 500 * 1.099, 500.0, england_and_wales]
    )


@pytest.mark.parametrize("region", ["NORTHERN IRELAND", "ATLANTIS", ""])
def test_unrecognised_regions_are_rejected(region):
    with pytest.raises(ValueError, match="unrecognised regions"):
        _uprated(["LONDON", region], [500.0, 500.0], 2025)


def test_a_dataset_without_water_charges_is_left_alone():
    previous_year = SimpleNamespace(household=pd.DataFrame({"rent": [1.0]}))
    current_year = SimpleNamespace(
        time_period="2025", household=pd.DataFrame({"region": ["SCOTLAND"]})
    )
    uprate_water_and_sewerage_charges(current_year, previous_year, parameters)
    assert "water_and_sewerage_charges" not in current_year.household


@settings(max_examples=200, deadline=None, derandomize=True)
@given(
    households=st.lists(
        st.tuples(
            st.sampled_from(REGIONS),
            st.floats(0, 5_000, allow_nan=False),
        ),
        min_size=1,
        max_size=30,
    ),
    year=st.sampled_from(UPRATED_YEARS),
    scale=st.floats(0, 10, allow_nan=False),
)
def test_water_uprating_properties(households, year, scale):
    """For every Region label, any charge of zero or more and every
    projected year:

    - the charge grows by its country's series, with the country taken from
      the model's `country` variable: Ofwat's for England, Wales and unknown
      regions, Scottish Water's for Scotland, and none for Northern Ireland;
    - each household's result depends only on its own row;
    - scaling every previous-year charge scales every result by the same
      factor.
    """
    regions, amounts = (list(column) for column in zip(*households))

    charges = _uprated(regions, amounts, year)

    expected = [
        amount * (1 + _expected_growth(region, year)) for region, amount in households
    ]
    assert charges == pytest.approx(expected)
    alone = [_uprated([region], [amount], year)[0] for region, amount in households]
    assert charges == pytest.approx(alone)
    scaled = _uprated(regions, [scale * amount for amount in amounts], year)
    assert scaled == pytest.approx(scale * charges)


def test_water_charges_are_uprated_once():
    # The country uprating replaces a single index: listing the column in
    # uprating_indices.yaml as well, or letting the index its variable
    # declares grow it after LEGACY_PROJECTION_END_YEAR, would apply a second
    # growth rate on top.
    listed = {name for names in _uprating_index_map().values() for name in names}
    assert "water_and_sewerage_charges" not in listed
    assert "water_and_sewerage_charges" not in _unmapped_uprating_indices(
        _uprating_index_map()
    )


def test_the_projection_fingerprint_covers_both_water_series():
    paths = uprating_input_paths()
    assert "gov.economic_assumptions.yoy_growth.ofwat.water_bills" in paths
    assert "gov.economic_assumptions.yoy_growth.scottish_water.water_bills" in paths


# A dataset with an unknown-region household cannot be projected forward until
# rent uprating handles Region.UNKNOWN (PolicyEngine/policyengine-uk#1985), so
# the dataset-level tests below use the twelve known regions.
KNOWN_REGIONS = [region for region in REGIONS if region != "UNKNOWN"]


def _one_household_per_known_region(charges, base_year=2024):
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
                "water_and_sewerage_charges": charges,
            }
        ),
        fiscal_year=base_year,
    )


def _compounded(amount, region, year, base_year=2024):
    return amount * np.prod(
        [1 + _expected_growth(region, y) for y in range(base_year + 1, year + 1)]
    )


def test_extended_dataset_compounds_each_country_water_growth():
    # Every projected year chains its country's growth, through the old
    # dataset horizon (2030) and the two years after it.
    extended = extend_single_year_dataset(
        _one_household_per_known_region(500.0), parameters, end_year=2032
    )

    for year in range(2025, PROJECTION_END_YEAR + 1):
        charges = extended[year].household["water_and_sewerage_charges"].to_numpy()
        assert charges == pytest.approx(
            [_compounded(500.0, region, year) for region in KNOWN_REGIONS]
        )
    assert PROJECTION_END_YEAR > LEGACY_PROJECTION_END_YEAR


def test_microsimulation_gives_scotland_scottish_water_growth():
    sim = Microsimulation(dataset=_one_household_per_known_region(500.0))

    charges = dict(
        zip(KNOWN_REGIONS, sim.calculate("water_and_sewerage_charges", 2026).values)
    )
    # 500 x 1.099 x 1.0867 in Scotland; Northern Ireland stays at 500.
    assert charges["SCOTLAND"] == pytest.approx(500 * 1.099 * 1.0867)
    assert charges["NORTHERN_IRELAND"] == 500.0
    assert charges["WALES"] == pytest.approx(charges["LONDON"])
    assert charges["LONDON"] == pytest.approx(
        500
        * (1 + ENGLAND_AND_WALES("2025-01-01"))
        * (1 + ENGLAND_AND_WALES("2026-01-01"))
    )


# WICS Final Determination 2027-33, physical pages 389-390 and 394:
# Table 163 and section 9.6.1/Table 171 assume that the West Central
# Bioresources conditions are met, without the uncertain-cost allowance.
# The real cap is 2.5% throughout: 2.5% core in 2027-2029, then 0.5% core
# plus 2.0% conditional WCB in 2030-2032. Add Table 164's charging CPI
# (3.2%, 2.1%, 1.9%, 2.0%, 2.0%, 2.0%) in percentage points. Section
# 9.5.12 uses prior-October CPI for 2027, then prior-September CPI from 2028.
# These are forecasts, not Scottish Water's later annual announcements.
# Table 174 (physical page 396) independently corroborates addition for
# the first two years: Band D 652.32 -> 689.50 -> 721.22. Its later years
# include uncertain-cost allowances and do not supply these expectations.
# Annual rates and cumulative factors from FY2026 were calculated with
# Decimal before model execution; no intermediate cash rounding is applied.
# https://www.wics.scot/system/files/2026-11/Final-Determination-2027-33-main-document.pdf#page=389
FINAL_SCOTTISH_CENTRAL_PROFILE = (
    (2027, 0.057, 1.057),
    (2028, 0.046, 1.105622),
    (2029, 0.044, 1.154269368),
    (2030, 0.045, 1.206211489560),
    (2031, 0.045, 1.260491006590200),
    (2032, 0.045, 1.317213101886759000),
)
FINAL_SCOTTISH_ANNUAL_RATES = [
    (year, growth) for year, growth, _ in FINAL_SCOTTISH_CENTRAL_PROFILE
]


@pytest.mark.parametrize("year, growth", FINAL_SCOTTISH_ANNUAL_RATES)
def test_final_scottish_water_growth_matches_wics_central_forecast(year, growth):
    """Pin the WCB-met, no-uncertain-cost forecast to the final source."""
    assert SCOTLAND(f"{year}-01-01") == pytest.approx(growth, abs=1e-12)


@pytest.mark.parametrize("year, growth", FINAL_SCOTTISH_ANNUAL_RATES)
def test_final_scottish_water_growth_keeps_country_controls(year, growth):
    charges = _uprated(
        ["SCOTLAND", "LONDON", "WALES", "NORTHERN_IRELAND", "UNKNOWN", "SCOTLAND"],
        [500.0, 500.0, 500.0, 500.0, 500.0, 0.0],
        year,
    )
    unchanged_ofwat = 500 * (1 + ENGLAND_AND_WALES(f"{year}-01-01"))
    assert charges == pytest.approx(
        [
            500 * (1 + growth),
            unchanged_ofwat,
            unchanged_ofwat,
            500,
            unchanged_ofwat,
            0,
        ],
        abs=0.01,
    )


def test_final_scottish_water_profile_compounds_from_2026_in_dataset():
    """Apply every final-source year, including years beyond the old horizon."""
    extended = extend_single_year_dataset(
        _one_household_per_known_region(500.0, base_year=2026),
        parameters,
        end_year=2032,
    )
    sim = Microsimulation(dataset=extended)

    for year, _, factor in FINAL_SCOTTISH_CENTRAL_PROFILE:
        unchanged_ofwat = 500 * np.prod(
            [
                1 + ENGLAND_AND_WALES(f"{previous_year}-01-01")
                for previous_year in range(2027, year + 1)
            ]
        )
        expected = [
            500 * factor
            if region == "SCOTLAND"
            else 500
            if region == "NORTHERN_IRELAND"
            else unchanged_ofwat
            for region in KNOWN_REGIONS
        ]
        np.testing.assert_allclose(
            extended[year].household["water_and_sewerage_charges"].to_numpy(),
            expected,
            rtol=0,
            atol=0.01,
            err_msg=f"Dataset water charges for {year}",
        )
        np.testing.assert_allclose(
            sim.calculate("water_and_sewerage_charges", year).values,
            expected,
            rtol=0,
            atol=0.01,
            err_msg=f"Microsimulation water charges for {year}",
        )
