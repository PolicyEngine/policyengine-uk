"""Tests for the BRMA a household gets when none is input.

brma (variables/household/BRMA.py) places a household with no BRMA input in
its region's entry in REGION_DEFAULT_BRMA, unless an earlier year's BRMA
carries forward. These properties hold for any households, regions by year,
BRMA inputs and order in which years are calculated:

1. The table is each region's BRMA with the most private-rented households in
   brma_private_rented_households.csv, a strict maximum, and it covers every
   region but UNKNOWN. A default gives the same LHA rates as inputting it.
2. Inputs win: in a year with a BRMA input, brma is that input.
3. Defaults: in a year with no BRMA input in it or before it, brma is the
   default for that year's region.
4. Membership: brma is either the default for that year's region or an
   input from that year or earlier made while the household was in the
   same region.
5. Carry forward: if the household's region has not changed since the
   latest input at or before a year, brma is that input. Where each region
   occupies one unbroken run of years, 2, 3 and 5 fix brma exactly.

Regions are input for every year so that region itself does not depend on
the order of calculation.
"""

from pathlib import Path

import pandas as pd
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

import policyengine_uk
from policyengine_uk import Simulation
from policyengine_uk.variables.household.BRMA import REGION_DEFAULT_BRMA
from policyengine_uk.variables.household.demographic.geography import Region
from policyengine_uk.variables.household.demographic.locations import BRMAName

PRIVATE_RENTED_HOUSEHOLDS = pd.read_csv(
    Path(policyengine_uk.__file__).parent
    / "parameters/gov/dwp/LHA/brma_private_rented_households.csv"
)
YEARS = list(range(2024, 2031))
REGIONS = [region.name for region in Region]
BRMAS = [brma.name for brma in BRMAName]
PROPERTY_SETTINGS = settings(
    max_examples=40,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)


def default_brma(region: str) -> str:
    defaults = {key.name: value.name for key, value in REGION_DEFAULT_BRMA.items()}
    return defaults.get(region, BRMAName.MAIDSTONE.name)


def simulate(regions_by_household, brma_inputs, years_to_calculate):
    """Return {year: [brma per household]} calculated in the given order."""
    people, benunits, households = {}, {}, {}
    for index, regions in enumerate(regions_by_household):
        person, benunit, household = f"p{index}", f"b{index}", f"h{index}"
        people[person] = {"age": {YEARS[0]: 40}}
        benunits[benunit] = {"members": [person]}
        households[household] = {
            "members": [person],
            "region": dict(zip(YEARS, regions)),
        }
        inputs = {year: values[index] for year, values in brma_inputs.items()}
        if inputs:
            households[household]["brma"] = inputs
    simulation = Simulation(
        situation={"people": people, "benunits": benunits, "households": households}
    )
    return {
        year: [str(value) for value in simulation.calculate("brma", year)]
        for year in years_to_calculate
    }


def brma_for(regions, brma, year):
    situation = {
        "people": {"adult": {"age": {2025: 40}}},
        "benunits": {"benunit": {"members": ["adult"]}},
        "households": {
            "household": {"members": ["adult"], "region": regions, "brma": brma}
        },
    }
    return str(Simulation(situation=situation).calculate("brma", year)[0])


def test_region_defaults_have_the_most_private_rented_households():
    households = PRIVATE_RENTED_HOUSEHOLDS.groupby(["region", "brma"]).households.sum()
    for region, brma in REGION_DEFAULT_BRMA.items():
        region_households = households.loc[region.name].sort_values(ascending=False)
        assert region_households.index[0] == brma.name, region
        # A strict maximum, so the table does not depend on tie-breaking.
        assert region_households.iloc[0] > region_households.iloc[1], region


def test_region_defaults_cover_every_region_but_unknown():
    assert set(REGION_DEFAULT_BRMA) == set(Region) - {Region.UNKNOWN}
    assert set(PRIVATE_RENTED_HOUSEHOLDS.region) == {
        region.name for region in REGION_DEFAULT_BRMA
    }
    assert set(PRIVATE_RENTED_HOUSEHOLDS.brma) == set(BRMAS)


@pytest.mark.parametrize("region", REGIONS)
def test_default_gives_the_same_lha_rates_as_inputting_it(region):
    def calculate(household_inputs):
        situation = {
            "people": {"adult": {"age": {2025: 40}}},
            "benunits": {"benunit": {"members": ["adult"]}},
            "households": {
                "household": {
                    "members": ["adult"],
                    "region": {2025: region},
                    "tenure_type": {2025: "RENT_PRIVATELY"},
                    "rent": {2025: 12_000},
                    **household_inputs,
                }
            },
        }
        simulation = Simulation(situation=situation)
        return [
            float(simulation.calculate(variable, 2025)[0])
            for variable in ("BRMA_LHA_rate", "uc_LHA_cap")
        ]

    defaulted = calculate({})
    assert defaulted[0] > 0
    assert defaulted == calculate({"brma": {2025: default_brma(region)}})


def test_input_carries_forward_to_later_years():
    # Region is input for 2025 only and carries forward like any input.
    regions = {2025: "SCOTLAND"}
    assert brma_for(regions, {2025: "GREATER_GLASGOW"}, 2026) == "GREATER_GLASGOW"
    assert brma_for(regions, {2025: "GREATER_GLASGOW"}, 2040) == "GREATER_GLASGOW"


def test_input_does_not_apply_to_earlier_years():
    regions = {2024: "SCOTLAND", 2025: "SCOTLAND"}
    assert brma_for(regions, {2025: "GREATER_GLASGOW"}, 2024) == "LOTHIAN"


def test_household_that_changes_region_gets_the_new_regions_default():
    regions = {2025: "SCOTLAND", 2026: "WALES"}
    assert brma_for(regions, {2025: "GREATER_GLASGOW"}, 2026) == "CARDIFF"


@st.composite
def scenarios(draw):
    household_count = draw(st.integers(1, 4))
    regions_by_household = []
    for _ in range(household_count):
        # Runs of years in one region; a region may recur after a move.
        regions = []
        while len(regions) < len(YEARS):
            region = draw(st.sampled_from(REGIONS))
            regions += [region] * draw(st.integers(1, len(YEARS)))
        regions_by_household.append(regions[: len(YEARS)])
    input_years = draw(st.sets(st.sampled_from(YEARS), max_size=3))
    brma_inputs = {
        year: [draw(st.sampled_from(BRMAS)) for _ in range(household_count)]
        for year in sorted(input_years)
    }
    order = draw(st.permutations(YEARS))
    return regions_by_household, brma_inputs, order


@PROPERTY_SETTINGS
@given(scenarios())
def test_brma_properties(scenario):
    regions_by_household, brma_inputs, order = scenario
    result = simulate(regions_by_household, brma_inputs, order)
    for index, regions in enumerate(regions_by_household):
        region_in = dict(zip(YEARS, regions))
        inputs = {year: values[index] for year, values in brma_inputs.items()}
        unbroken_runs = all(
            regions.index(region) + regions.count(region) - 1
            == len(regions) - 1 - regions[::-1].index(region)
            for region in set(regions)
        )
        for year in YEARS:
            brma = result[year][index]
            default = default_brma(region_in[year])
            earlier_inputs = [past for past in inputs if past <= year]
            if year in inputs:
                assert brma == inputs[year]
            if not earlier_inputs:
                assert brma == default
            assert brma == default or any(
                brma == inputs[past] and region_in[past] == region_in[year]
                for past in earlier_inputs
            )
            if earlier_inputs:
                latest = max(earlier_inputs)
                unchanged = all(
                    region_in[between] == region_in[year]
                    for between in range(latest, year + 1)
                )
                if unchanged:
                    assert brma == inputs[latest]
                elif unbroken_runs:
                    assert brma == default
