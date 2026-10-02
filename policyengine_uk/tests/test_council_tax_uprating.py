from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from policyengine_uk import Microsimulation, Simulation, parameters
from policyengine_uk.data import UKSingleYearDataset
from policyengine_uk.data.economic_assumptions import (
    extend_single_year_dataset,
    uprate_council_tax,
)
from policyengine_uk.variables.household.demographic.geography import Region


REGIONS = [region.name for region in Region]
UPRATED_YEARS = list(range(2023, 2031))
COUNCIL_TAX_GROWTH = parameters.gov.economic_assumptions.yoy_growth.obr.council_tax


def _country_of_each_region():
    # The model's own region-to-country mapping (the `country` variable), so
    # the expected growth below comes from a second path to the one the
    # uprating code takes.
    people = {f"person_{region}": {"age": 40} for region in REGIONS}
    households = {
        f"household_{region}": {"members": [f"person_{region}"], "region": region}
        for region in REGIONS
    }
    sim = Simulation(situation={"people": people, "households": households})
    countries = sim.calculate("country", 2025)
    return dict(zip(REGIONS, countries))


COUNTRY = _country_of_each_region()


def _expected_growth(region, year):
    # Council tax exists in England, Scotland and Wales; OBR forecasts it for
    # each. Northern Ireland levies domestic rates instead, so its council tax
    # has no growth. An unknown region takes England's.
    country = COUNTRY[region]
    if country == "NORTHERN_IRELAND":
        return 0.0
    series = "england" if country == "UNKNOWN" else country.lower()
    return COUNCIL_TAX_GROWTH.get_child(series)(year)


def _uprated_council_tax(regions, council_tax, year):
    previous_year = SimpleNamespace(
        household=pd.DataFrame({"council_tax": council_tax}, dtype=float)
    )
    current_year = SimpleNamespace(
        time_period=str(year),
        household=pd.DataFrame(
            {"region": regions, "council_tax": [0.0] * len(council_tax)}
        ),
    )
    uprate_council_tax(current_year, previous_year, parameters)
    return current_year.household["council_tax"].to_numpy()


def test_uprate_council_tax_holds_northern_ireland_flat():
    # Northern Ireland used to fall through to England's growth (1,070.2),
    # because the code compared the region with "NORTHERN IRELAND" (a space)
    # while the dataset label is NORTHERN_IRELAND.
    council_tax = _uprated_council_tax(
        ["LONDON", "WALES", "SCOTLAND", "NORTHERN_IRELAND"], [1_000.0] * 4, 2025
    )

    assert council_tax == pytest.approx([1_070.2, 1_077.3, 1_038.4, 1_000.0])


def test_uprate_council_tax_gives_unknown_region_england_growth():
    council_tax = _uprated_council_tax(["UNKNOWN"], [1_000.0], 2025)

    assert council_tax == pytest.approx([1_070.2])


@pytest.mark.parametrize("region", ["NORTHERN IRELAND", "ATLANTIS", ""])
def test_uprate_council_tax_rejects_unrecognised_regions(region):
    # An unrecognised label used to get England's growth silently, which is
    # how the Northern Ireland typo went unnoticed.
    with pytest.raises(ValueError, match="unrecognised regions"):
        _uprated_council_tax(["LONDON", region], [1_000.0, 1_000.0], 2025)


@settings(max_examples=200, deadline=None, derandomize=True)
@given(
    households=st.lists(
        st.tuples(
            st.sampled_from(REGIONS),
            st.floats(0, 50_000, allow_nan=False),
        ),
        min_size=1,
        max_size=30,
    ),
    year=st.sampled_from(UPRATED_YEARS),
    scale=st.floats(0, 10, allow_nan=False),
)
def test_uprate_council_tax_properties(households, year, scale):
    """For every region in the Region enum, any council tax of zero or more
    and every uprated year:

    - council tax grows by its country's OBR series, with the country taken
      from the model's `country` variable: England's for English regions and
      unknown regions, Scotland's and Wales's for those countries, and none
      for Northern Ireland;
    - a Northern Ireland household's council tax is unchanged;
    - each household's result depends only on its own row;
    - scaling every previous-year amount scales every result by the same
      factor.
    """
    regions, amounts = (list(column) for column in zip(*households))

    council_tax = _uprated_council_tax(regions, amounts, year)

    expected = [
        amount * (1 + _expected_growth(region, year)) for region, amount in households
    ]
    assert council_tax == pytest.approx(expected)
    northern_ireland = np.array(regions) == "NORTHERN_IRELAND"
    assert (council_tax[northern_ireland] == np.array(amounts)[northern_ireland]).all()
    alone = [
        _uprated_council_tax([region], [amount], year)[0]
        for region, amount in households
    ]
    assert council_tax == pytest.approx(alone)
    scaled = _uprated_council_tax(regions, [scale * amount for amount in amounts], year)
    assert scaled == pytest.approx(scale * council_tax)


# A dataset with an unknown-region household cannot be projected forward until
# rent uprating handles Region.UNKNOWN (PolicyEngine/policyengine-uk#1985), so
# the dataset-level tests below use the twelve known regions.
KNOWN_REGIONS = [region for region in REGIONS if region != "UNKNOWN"]


def _one_household_per_known_region(council_tax):
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
                "council_tax": council_tax,
            }
        ),
        fiscal_year=2023,
    )


def _compounded(amount, region, year, base_year=2023):
    return amount * np.prod(
        [1 + _expected_growth(region, y) for y in range(base_year + 1, year + 1)]
    )


def test_extended_dataset_compounds_each_country_council_tax_growth():
    # Projecting a dataset forward chains the yearly uprating, so each year's
    # council tax is the base amount times the product of its country's
    # growth factors since the base year.
    extended = extend_single_year_dataset(
        _one_household_per_known_region(1_500.0), parameters, end_year=2030
    )

    for year in range(2024, 2031):
        council_tax = extended[year].household["council_tax"].to_numpy()
        assert council_tax == pytest.approx(
            [_compounded(1_500.0, region, year) for region in KNOWN_REGIONS]
        )
        assert council_tax[KNOWN_REGIONS.index("NORTHERN_IRELAND")] == 1_500.0


def test_microsimulation_holds_northern_ireland_council_tax_flat():
    sim = Microsimulation(dataset=_one_household_per_known_region(1_500.0))

    for year in (2026, 2030):
        council_tax = sim.calculate("council_tax", year).values
        assert council_tax == pytest.approx(
            [_compounded(1_500.0, region, year) for region in KNOWN_REGIONS]
        )
        council_tax = dict(zip(KNOWN_REGIONS, council_tax))
        assert council_tax["NORTHERN_IRELAND"] == 1_500.0
        assert council_tax["LONDON"] > 1_500.0
