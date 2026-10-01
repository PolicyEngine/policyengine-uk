"""Tests for the BRMA a household gets when none is input.

brma (variables/household/BRMA.py) places a household with no BRMA input in
its region's entry in REGION_DEFAULT_BRMA, unless an earlier year's BRMA
carries forward. These properties hold for any households, regions by year,
BRMA inputs and order in which years are calculated:

1. The table is the list of rents' most common BRMA in each region, every
   BRMA in it lies in its own region, and it covers every region but UNKNOWN.
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

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.parameters.gov.dwp.LHA import lha_list_of_rents
from policyengine_uk.variables.household.BRMA import REGION_DEFAULT_BRMA
from policyengine_uk.variables.household.demographic.geography import Region
from policyengine_uk.variables.household.demographic.locations import BRMAName

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


def test_region_defaults_are_the_most_common_brma_in_the_list_of_rents():
    counts = lha_list_of_rents.groupby(["region", "brma"]).size()
    for region, brma in REGION_DEFAULT_BRMA.items():
        region_counts = counts.loc[region.name].sort_values(ascending=False)
        assert region_counts.index[0] == brma.name, region
        # A strict maximum, so the table does not depend on tie-breaking.
        assert region_counts.iloc[0] > region_counts.iloc[1], region


def test_region_defaults_cover_every_region_but_unknown():
    assert set(REGION_DEFAULT_BRMA) == set(Region) - {Region.UNKNOWN}
    assert set(lha_list_of_rents.region.unique()) == {
        region.name for region in REGION_DEFAULT_BRMA
    }


def test_no_brma_spans_two_regions():
    regions_per_brma = lha_list_of_rents.groupby("brma").region.nunique()
    assert regions_per_brma.max() == 1
    region_of = lha_list_of_rents.groupby("brma").region.first()
    for region, brma in REGION_DEFAULT_BRMA.items():
        assert region_of[brma.name] == region.name


def test_input_carries_forward_to_later_years():
    # Region is input for 2025 only and carries forward like any input.
    regions = {2025: "SCOTLAND"}
    assert brma_for(regions, {2025: "LOTHIAN"}, 2026) == "LOTHIAN"
    assert brma_for(regions, {2025: "LOTHIAN"}, 2040) == "LOTHIAN"


def test_input_does_not_apply_to_earlier_years():
    regions = {2024: "SCOTLAND", 2025: "SCOTLAND"}
    assert brma_for(regions, {2025: "LOTHIAN"}, 2024) == "ABERDEEN_AND_SHIRE"


def test_household_that_changes_region_gets_the_new_regions_default():
    regions = {2025: "SCOTLAND", 2026: "WALES"}
    assert brma_for(regions, {2025: "LOTHIAN"}, 2026) == "CARDIFF"


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
