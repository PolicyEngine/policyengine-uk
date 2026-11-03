"""Tests for the BRMA a household gets when none is input.

brma (variables/household/BRMA.py) places a household with no BRMA input in
its region's entry in REGION_DEFAULT_BRMA, unless an earlier year's BRMA
carries forward.

1. The table is each region's BRMA with the most private-rented households in
   brma_private_rented_households.csv.gz, a strict maximum, and it covers every
   region but UNKNOWN. A default gives the same LHA rates as inputting it.
2. The rule: in a year with a BRMA input, brma is that input. Otherwise, if
   there is an earlier input and the household's region has been the same in
   every year from the latest one to this year, brma is that input; if not,
   brma is the default for this year's region.

Each year's region is the latest region input at or before it, or London
(region's default) if there is none. brma reads stored values only, so the
rule holds in any order of calculation, and calculating brma never changes any
year's region. Like core's own input handling, it assumes every household has
BRMA inputs in the same years (or none) and region inputs in the same years:
core fills a household missing from a year's input with the default.
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
    / "parameters/gov/dwp/LHA/brma_private_rented_households.csv.gz"
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


def test_input_carries_forward_when_region_was_input_earlier():
    regions = {2024: "SCOTLAND"}
    assert brma_for(regions, {2025: "GREATER_GLASGOW"}, 2026) == "GREATER_GLASGOW"
    assert brma_for(regions, {2025: "GREATER_GLASGOW"}, 2040) == "GREATER_GLASGOW"


def test_input_does_not_apply_to_earlier_years():
    regions = {2024: "SCOTLAND", 2025: "SCOTLAND"}
    assert brma_for(regions, {2025: "GREATER_GLASGOW"}, 2024) == "LOTHIAN"


def test_household_that_changes_region_gets_the_new_regions_default():
    regions = {2025: "SCOTLAND", 2026: "WALES"}
    assert brma_for(regions, {2025: "GREATER_GLASGOW"}, 2026) == "CARDIFF"
    # The move counts even when the BRMA's own year has no region known.
    regions = {2024: "SCOTLAND", 2026: "WALES"}
    assert brma_for(regions, {2025: "GREATER_GLASGOW"}, 2026) == "CARDIFF"


def test_household_that_returns_to_a_region_gets_its_default_in_any_order():
    regions = {2026: "SCOTLAND", 2027: "WALES", 2028: "SCOTLAND"}
    brma = {2026: "GREATER_GLASGOW"}
    assert brma_for(regions, brma, 2028) == "LOTHIAN"
    situation = {
        "people": {"adult": {"age": {2026: 40}}},
        "benunits": {"benunit": {"members": ["adult"]}},
        "households": {
            "household": {"members": ["adult"], "region": regions, "brma": brma}
        },
    }
    simulation = Simulation(situation=situation)
    assert [str(simulation.calculate("brma", year)[0]) for year in (2027, 2028)] == [
        "CARDIFF",
        "LOTHIAN",
    ]


def test_calculating_brma_does_not_change_region_or_other_results():
    # Region input in 2024 only and a BRMA input in 2025: brma for later years
    # must not calculate 2025's region after a later year's, which core would
    # answer with region's default (London).
    def simulation():
        return Simulation(
            situation={
                "people": {"adult": {"age": {2024: 40}, "employment_income": 50_000}},
                "benunits": {"benunit": {"members": ["adult"]}},
                "households": {
                    "household": {
                        "members": ["adult"],
                        "region": {2024: "SCOTLAND"},
                        "brma": {2025: "GREATER_GLASGOW", 2026: "LOTHIAN"},
                        "tenure_type": {2024: "RENT_PRIVATELY"},
                        "rent": {2024: 12_000},
                    }
                },
            }
        )

    fresh = simulation()
    expected_tax = float(fresh.calculate("income_tax", 2025)[0])
    tested = simulation()
    tested.calculate("BRMA_LHA_rate", 2026)
    assert str(tested.calculate("brma", 2027)[0]) == "LOTHIAN"
    assert str(tested.calculate("region", 2025)[0]) == "SCOTLAND"
    assert str(tested.calculate("region", 2026)[0]) == "SCOTLAND"
    assert float(tested.calculate("income_tax", 2025)[0]) == expected_tax


def test_calculating_brma_without_inputs_does_not_change_region_or_tax():
    def simulation():
        return Simulation(
            situation={
                "people": {
                    "p": {"age": {2024: 40}, "employment_income": {2025: 50_000}}
                },
                "benunits": {"b": {"members": ["p"]}},
                "households": {"h": {"members": ["p"], "region": {2024: "SCOTLAND"}}},
            }
        )

    expected_tax = float(simulation().calculate("income_tax", 2025)[0])
    tested = simulation()
    assert str(tested.calculate("brma", 2026)[0]) == "LOTHIAN"
    assert str(tested.calculate("region", 2025)[0]) == "SCOTLAND"
    assert float(tested.calculate("income_tax", 2025)[0]) == expected_tax


def test_region_carries_forward_until_its_next_input():
    regions = {2024: "SCOTLAND", 2026: "WALES"}
    situation = {
        "people": {"adult": {"age": {2024: 40}}},
        "benunits": {"benunit": {"members": ["adult"]}},
        "households": {"household": {"members": ["adult"], "region": regions}},
    }
    simulation = Simulation(situation=situation)
    assert [str(simulation.calculate("brma", year)[0]) for year in (2025, 2026)] == [
        "LOTHIAN",
        "CARDIFF",
    ]


def test_brma_stored_only_on_another_branch_is_not_carried():
    simulation = Simulation(
        situation={
            "people": {"adult": {"age": {2024: 40}}},
            "benunits": {"benunit": {"members": ["adult"]}},
            "households": {
                "household": {
                    "members": ["adult"],
                    "region": {2024: "SCOTLAND"},
                    "brma": {2024: "GREATER_GLASGOW"},
                }
            },
        }
    )
    child = simulation.get_branch("child")
    # More years than core's spiral limit, all stored only on the child.
    for year in range(2025, 2036):
        child.calculate("brma", year)
    sibling = child.get_branch("default")
    assert str(sibling.calculate("brma", 2036)[0]) == "GREATER_GLASGOW"
    assert str(simulation.calculate("brma", 2036)[0]) == "GREATER_GLASGOW"


def expected_brma(regions, inputs, year):
    """The rule, given the region each year resolves to and the BRMA inputs."""
    if year in inputs:
        return inputs[year]
    earlier = [past for past in inputs if past < year]
    if earlier:
        latest = max(earlier)
        if all(regions[between] == regions[year] for between in range(latest, year)):
            return inputs[latest]
    return default_brma(regions[year])


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
def test_brma_follows_the_rule_in_any_order(scenario):
    regions_by_household, brma_inputs, order = scenario
    result = simulate(regions_by_household, brma_inputs, order)
    for index, regions in enumerate(regions_by_household):
        region_in = dict(zip(YEARS, regions))
        inputs = {year: values[index] for year, values in brma_inputs.items()}
        for year in YEARS:
            assert result[year][index] == expected_brma(region_in, inputs, year)


def build(region_inputs_by_household, brma_inputs):
    people, benunits, households = {}, {}, {}
    for index, region_inputs in enumerate(region_inputs_by_household):
        person, benunit, household = f"p{index}", f"b{index}", f"h{index}"
        people[person] = {"age": {YEARS[0]: 40}}
        benunits[benunit] = {"members": [person]}
        households[household] = {"members": [person]}
        if region_inputs:
            households[household]["region"] = region_inputs
        inputs = {year: values[index] for year, values in brma_inputs.items()}
        if inputs:
            households[household]["brma"] = inputs
    return Simulation(
        situation={"people": people, "benunits": benunits, "households": households}
    )


@st.composite
def sparse_scenarios(draw):
    household_count = draw(st.integers(1, 4))
    region_years = sorted(draw(st.sets(st.sampled_from(YEARS), max_size=3)))
    region_inputs_by_household = [
        {year: draw(st.sampled_from(REGIONS)) for year in region_years}
        for _ in range(household_count)
    ]
    input_years = draw(st.sets(st.sampled_from(YEARS), max_size=3))
    brma_inputs = {
        year: [draw(st.sampled_from(BRMAS)) for _ in range(household_count)]
        for year in sorted(input_years)
    }
    order = draw(st.permutations(YEARS))
    return region_inputs_by_household, brma_inputs, order


@PROPERTY_SETTINGS
@given(sparse_scenarios())
def test_brma_with_sparse_regions_follows_the_rule_and_keeps_regions(scenario):
    region_inputs_by_household, brma_inputs, order = scenario
    fresh = build(region_inputs_by_household, brma_inputs)
    fresh_regions = {
        year: [str(value) for value in fresh.calculate("region", year)]
        for year in YEARS
    }
    tested = build(region_inputs_by_household, brma_inputs)
    result = {
        year: [str(value) for value in tested.calculate("brma", year)] for year in order
    }
    for year in YEARS:
        regions_after = [str(value) for value in tested.calculate("region", year)]
        assert regions_after == fresh_regions[year]
    for index, region_inputs in enumerate(region_inputs_by_household):
        # The region in effect each year: the latest input at or before it, or
        # region's default (London). Core's own carry-over can instead give
        # the default for a year that has a later input
        # (policyengine-core#562); brma follows the inputs.
        regions = {
            year: region_inputs[max(past for past in region_inputs if past <= year)]
            if any(past <= year for past in region_inputs)
            else "LONDON"
            for year in YEARS
        }
        inputs = {year: values[index] for year, values in brma_inputs.items()}
        for year in YEARS:
            assert result[year][index] == expected_brma(regions, inputs, year)
