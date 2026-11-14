"""A household's share of a national total does not depend on who is simulated.

Business rates, corporate SDLT, corporate land, carbon tax's corporate part,
the reform lumps borne by capital and by consumers, employer National
Insurance's capital and consumer responses and the three public spending
changes each spread a national total over households by a population key.
A household situation has no population to take a share of, so each is 0 in a
situation, whatever the household's weight and however many axis points it
has, unless the share is set as an input (policyengine-uk#2896).
"""

import copy

import numpy as np
import pandas as pd
import pytest

from policyengine_uk import Simulation
from policyengine_uk.data import UKSingleYearDataset

YEAR = 2026

# The household in policyengine-uk#2896.
ISSUE_HOUSEHOLD = {
    "people": {"adult": {"age": {YEAR: 45}, "employment_income": {YEAR: 40_000}}},
    "benunits": {"bu": {"members": ["adult"]}},
    "households": {
        "hh": {
            "members": ["adult"],
            "region": {YEAR: "LONDON"},
            "private_pension_wealth": {YEAR: 50_000},
        }
    },
}

# A household that holds both keys: corporate-sector wealth and consumption.
HOLDER = copy.deepcopy(ISSUE_HOUSEHOLD)
HOLDER["households"]["hh"].update(
    {
        "corporate_wealth": {YEAR: 20_000},
        "food_and_non_alcoholic_beverages_consumption": {YEAR: 5_000},
        "transport_consumption": {YEAR: 3_000},
    }
)

EMPLOYER_NI = {
    "gov.hmrc.national_insurance.class_1.employer_scale[1].rate": {YEAR: 0.25},
    "gov.contrib.policyengine.employer_ni.employee_incidence": {YEAR: 0},
}

# Each term, with a reform under which a household holding the keys takes a
# non-zero part of it as part of a population.
CASES = {
    "shareholding": {},
    "consumption_shareholding": {},
    "corporate_land_value": {},
    "business_rates": {},
    "corporate_sdlt": {},
    "corporate_incident_tax_revenue_change": {
        "gov.contrib.policyengine.budget.corporate_incident_tax_change": {YEAR: 1}
    },
    "consumer_incident_tax_revenue_change": {
        "gov.contrib.policyengine.budget.consumer_incident_tax_change": {YEAR: 1}
    },
    # With no consumer incidence, all of the tax is the corporate part.
    "carbon_tax": {
        "gov.contrib.ubi_center.carbon_tax.rate": {YEAR: 100},
        "gov.contrib.ubi_center.carbon_tax.consumer_incidence": {YEAR: 0},
    },
    # The household owns no land of its own, so its tax is on corporate land.
    "LVT": {"gov.contrib.ubi_center.land_value_tax.corporate_rate": {YEAR: 0.01}},
    "employer_ni_response_capital_incidence": EMPLOYER_NI,
    "employer_ni_response_consumer_incidence": EMPLOYER_NI,
    "nhs_budget_change": {"gov.contrib.policyengine.budget.nhs": {YEAR: 1}},
    "education_budget_change": {"gov.contrib.policyengine.budget.education": {YEAR: 1}},
    "other_public_spending_budget_change": {
        "gov.contrib.policyengine.budget.other_public_spending": {YEAR: 1}
    },
}


def calculate(sim, variable):
    return np.asarray(sim.calculate(variable, YEAR, map_to="household"))


def in_situation(situation, variable, reform=None):
    return calculate(Simulation(situation=situation, reform=reform or None), variable)


def as_population(situation, variable, reform=None):
    """The situation's household as a dataset in which it stands for ten million
    households, so that its share of each total is small, as in the data. As
    the whole UK it would bear every UK total and rank below the deciles."""
    household = situation["households"]["hh"]
    adult = situation["people"]["adult"]
    dataset = UKSingleYearDataset(
        person=pd.DataFrame(
            {
                "person_id": [1],
                "person_benunit_id": [1],
                "person_household_id": [1],
                **{name: [value[YEAR]] for name, value in adult.items()},
            }
        ),
        benunit=pd.DataFrame({"benunit_id": [1]}),
        household=pd.DataFrame(
            {
                "household_id": [1],
                "household_weight": [1e7],
                # Columns dataset uprating reads.
                "council_tax": [0.0],
                "rent": [0.0],
                "tenure_type": ["OWNED_OUTRIGHT"],
                "household_owns_tv": [False],
                **{
                    name: [value[YEAR]]
                    for name, value in household.items()
                    if name != "members"
                },
            }
        ),
        fiscal_year=YEAR,
    )
    return calculate(Simulation(dataset=dataset, reform=reform or None), variable)


def copies(situation, weights):
    """The situation's household once per weight, each with that weight."""
    household = situation["households"]["hh"]
    adult = situation["people"]["adult"]
    out = {"people": {}, "benunits": {}, "households": {}}
    for i, weight in enumerate(weights):
        out["people"][f"adult_{i}"] = copy.deepcopy(adult)
        out["benunits"][f"bu_{i}"] = {"members": [f"adult_{i}"]}
        out["households"][f"hh_{i}"] = {
            **copy.deepcopy(household),
            "members": [f"adult_{i}"],
            "household_weight": {YEAR: weight},
        }
    return out


def test_situation_with_pension_wealth_takes_no_corporate_share():
    """The reproducer in policyengine-uk#2896: one household with pension wealth
    was handed every UK total and a household_net_income of about -£40.77bn."""
    sim = Simulation(situation=ISSUE_HOUSEHOLD)
    for variable in ["shareholding", "business_rates", "corporate_sdlt"]:
        assert calculate(sim, variable) == pytest.approx([0])
    without_pension_wealth = copy.deepcopy(ISSUE_HOUSEHOLD)
    del without_pension_wealth["households"]["hh"]["private_pension_wealth"]
    assert calculate(sim, "household_net_income") == pytest.approx(
        in_situation(without_pension_wealth, "household_net_income")
    )

    # Under a 1% land value tax it pays nothing, since it owns no land.
    land_value_tax = {"gov.contrib.ubi_center.land_value_tax.rate": {YEAR: 0.01}}
    taxed = Simulation(situation=ISSUE_HOUSEHOLD, reform=land_value_tax)
    assert calculate(taxed, "LVT") == pytest.approx([0])
    assert calculate(taxed, "hbai_household_net_income") == pytest.approx(
        calculate(sim, "hbai_household_net_income")
    )


@pytest.mark.parametrize("variable", sorted(CASES))
def test_situation_takes_no_share_whatever_its_weight(variable):
    reform = CASES[variable]
    # As part of a population, the household takes a part of the total.
    assert as_population(HOLDER, variable, reform)[0] != 0
    # As situations, households of weight 1, 1,000 and 0 take none.
    values = in_situation(copies(HOLDER, [1, 1_000, 0]), variable, reform)
    assert values == pytest.approx([0, 0, 0])


@pytest.mark.parametrize("variable", sorted(CASES))
def test_situation_takes_no_share_at_any_axis_point(variable):
    situation = copy.deepcopy(HOLDER)
    situation["axes"] = [
        [
            {
                "name": "employment_income",
                "count": 9,
                "min": 0,
                "max": 80_000,
                "period": YEAR,
            }
        ]
    ]
    assert in_situation(situation, variable, CASES[variable]) == pytest.approx(
        np.zeros(9)
    )


# Synthetic totals make each allocation checkable by hand.
SYNTHETIC_TOTALS = {
    "gov.hmrc.business_rates.statistics.revenue.ENGLAND": {YEAR: 100},
    "gov.hmrc.business_rates.statistics.revenue.ENGLAND_CENTRAL_LIST": {YEAR: 0},
    "gov.hmrc.business_rates.statistics.revenue.SCOTLAND": {YEAR: 0},
    "gov.hmrc.business_rates.statistics.revenue.WALES": {YEAR: 0},
    "gov.hmrc.business_rates.statistics.revenue.WALES_CENTRAL_LIST": {YEAR: 0},
    "gov.hmrc.business_rates.statistics.revenue.NORTHERN_IRELAND": {YEAR: 0},
    "gov.hmrc.stamp_duty.statistics.residential.corporate.revenue": {YEAR: 20},
    "gov.hmrc.stamp_duty.statistics.non_residential.corporate.revenue": {YEAR: 30},
    "household.wealth.land.value.aggregate_corporate_land_value": {YEAR: 1_000},
    **CASES["corporate_incident_tax_revenue_change"],
    **CASES["consumer_incident_tax_revenue_change"],
    **CASES["carbon_tax"],
    **EMPLOYER_NI,
}


def test_situation_honours_a_set_share():
    situation = copy.deepcopy(HOLDER)
    situation["households"]["hh"]["shareholding"] = {YEAR: 1e-6}
    situation["households"]["hh"]["consumption_shareholding"] = {YEAR: 2e-6}
    sim = Simulation(situation=situation, reform=SYNTHETIC_TOTALS)

    system = sim.tax_benefit_system
    sector_emissions = system.parameters(f"{YEAR}-01-01").household.consumption.carbon
    uk_emissions = sum(
        sector_emissions.emissions[category.replace("_consumption", "")]
        for category in system.get_variable("consumption").adds
    )
    expected = {
        "business_rates": 1e-6 * 100,
        "corporate_sdlt": 1e-6 * (20 + 30),
        "corporate_land_value": 1e-6 * 1_000,
        "corporate_incident_tax_revenue_change": 1e-6 * 1e9,
        "carbon_tax": 1e-6 * 100 * uk_emissions,
        "consumer_incident_tax_revenue_change": 2e-6 * 1e9,
        # Employer NI's total is the simulation's own, so a situation never
        # takes a share of it.
        "employer_ni_response_capital_incidence": 0,
        "employer_ni_response_consumer_incidence": 0,
    }
    for variable, value in expected.items():
        assert calculate(sim, variable) == pytest.approx([value], rel=1e-5), variable


def test_situation_decile_uses_the_fixed_bounds_whatever_the_weight():
    deciles = in_situation(
        copies(HOLDER, [1, 1_000, 0]), "pre_budget_change_ons_household_income_decile"
    )
    assert deciles[0] == deciles[1] == deciles[2]
    assert 1 <= deciles[0] <= 10


# Runs of part of the UK, with the UK totals carried by the data.

# Four households in two regions, whose keys differ. Each stands for millions,
# as survey households do, so no one bears much of any UK total.
POPULATION = [
    {
        "region": "LONDON",
        "corporate_wealth": 100_000,
        "private_pension_wealth": 50_000,
        "food_and_non_alcoholic_beverages_consumption": 4_000,
        "transport_consumption": 2_000,
        "household_weight": 3e6,
        "employment_income": 40_000,
    },
    {
        "region": "LONDON",
        "corporate_wealth": 0,
        "private_pension_wealth": 200_000,
        "food_and_non_alcoholic_beverages_consumption": 6_000,
        "transport_consumption": 1_000,
        "household_weight": 5e6,
        "employment_income": 20_000,
    },
    {
        "region": "WALES",
        "corporate_wealth": 300_000,
        "private_pension_wealth": 0,
        "food_and_non_alcoholic_beverages_consumption": 3_000,
        "transport_consumption": 4_000,
        "household_weight": 2e6,
        "employment_income": 60_000,
    },
    {
        "region": "WALES",
        "corporate_wealth": 10_000,
        "private_pension_wealth": 20_000,
        "food_and_non_alcoholic_beverages_consumption": 5_000,
        "transport_consumption": 500,
        "household_weight": 4e6,
        "employment_income": 30_000,
    },
]

# Every term spread by a population key, under one reform.
SPREAD = [
    "shareholding",
    "consumption_shareholding",
    "corporate_land_value",
    "business_rates",
    "corporate_sdlt",
    "corporate_incident_tax_revenue_change",
    "consumer_incident_tax_revenue_change",
    "carbon_tax",
    "LVT",
]
SPREAD_REFORM = {
    **CASES["corporate_incident_tax_revenue_change"],
    **CASES["consumer_incident_tax_revenue_change"],
    **CASES["LVT"],
    "gov.contrib.ubi_center.carbon_tax.rate": {YEAR: 100},
    "gov.contrib.ubi_center.carbon_tax.consumer_incidence": {YEAR: 0.5},
}


def hand_totals(rows):
    """The UK total of each key component over ``rows``, at their weights."""
    from policyengine_uk.utils.uk_totals import KEYS, components, total_name

    return {
        total_name(component): sum(
            row.get(component, 0) * row["household_weight"] for row in rows
        )
        for key in KEYS
        for component in components(key)
    }


def population_dataset(rows, carried=None, year=YEAR):
    """A dataset of ``rows``, one person per household, with the UK totals
    ``carried`` written on every household."""
    n = len(rows)
    ids = list(range(1, n + 1))
    household = {
        "household_id": ids,
        # Columns dataset uprating reads.
        "council_tax": [0.0] * n,
        "rent": [0.0] * n,
        "tenure_type": ["OWNED_OUTRIGHT"] * n,
        "household_owns_tv": [False] * n,
    }
    for name in rows[0]:
        if name != "employment_income":
            household[name] = [row[name] for row in rows]
    for name, value in (carried or {}).items():
        household[name] = [value] * n
    return UKSingleYearDataset(
        person=pd.DataFrame(
            {
                "person_id": ids,
                "person_benunit_id": ids,
                "person_household_id": ids,
                "age": [45] * n,
                "employment_income": [row["employment_income"] for row in rows],
            }
        ),
        benunit=pd.DataFrame({"benunit_id": ids}),
        household=pd.DataFrame(household),
        fiscal_year=year,
    )


def population_simulation(rows, carried=None, year=YEAR, reform=SPREAD_REFORM):
    """A simulation built from ``population_dataset``."""
    return Simulation(dataset=population_dataset(rows, carried, year), reform=reform)


def spread_values(sim, year=YEAR):
    return {variable: calculate_at(sim, variable, year) for variable in SPREAD}


def calculate_at(sim, variable, year):
    return np.asarray(sim.calculate(variable, year, map_to="household"))


def test_part_of_the_uk_carrying_the_uk_totals_gets_its_national_shares():
    whole = spread_values(population_simulation(POPULATION))
    # Wales on its own, as a region filtered from the data.
    wales = spread_values(
        population_simulation(POPULATION[2:], carried=hand_totals(POPULATION))
    )
    for variable in SPREAD:
        assert whole[variable][2:].any(), variable
        assert wales[variable] == pytest.approx(whole[variable][2:], rel=1e-5), variable


def test_blocks_carrying_the_pool_totals_match_the_unblocked_run():
    """As a build runs a pool in blocks, each block's weights scaled up to the
    pool's mass: carrying the pool's totals, a block gives each household what
    the whole pool gives it, whichever households the block holds."""
    pool = spread_values(population_simulation(POPULATION))
    totals = hand_totals(POPULATION)
    pool_mass = sum(row["household_weight"] for row in POPULATION)
    for block in (POPULATION[:2], POPULATION[2:]):
        scale = pool_mass / sum(row["household_weight"] for row in block)
        scaled = [
            {**row, "household_weight": row["household_weight"] * scale}
            for row in block
        ]
        values = spread_values(population_simulation(scaled, carried=totals))
        start = POPULATION.index(block[0])
        for variable in SPREAD:
            assert values[variable] == pytest.approx(
                pool[variable][start : start + len(block)], rel=1e-5
            ), variable


def test_whole_uk_carrying_its_totals_matches_the_weighted_branch():
    without = spread_values(population_simulation(POPULATION))
    carrying = spread_values(
        population_simulation(POPULATION, carried=hand_totals(POPULATION))
    )
    for variable in SPREAD:
        assert carrying[variable] == pytest.approx(without[variable], rel=1e-5), (
            variable
        )


def test_carried_totals_project_with_the_data():
    """Totals written at the dataset's year grow as the weighted totals of the
    projected data do, so a later year's shares still match."""
    base_year, later = 2024, 2027
    whole = population_simulation(POPULATION, year=base_year)
    wales = population_simulation(
        POPULATION[2:], carried=hand_totals(POPULATION), year=base_year
    )
    for variable in ["shareholding", "consumption_shareholding", "carbon_tax"]:
        assert calculate_at(wales, variable, later) == pytest.approx(
            calculate_at(whole, variable, later)[2:], rel=1e-4
        ), variable


def test_situation_carrying_uk_totals_gets_its_share():
    situation = copies(HOLDER, [1, 1_000])
    totals = {
        "uk_total_corporate_wealth": 4e12,
        "uk_total_private_pension_wealth": 6e12,
        "uk_total_food_and_non_alcoholic_beverages_consumption": 1e11,
        "uk_total_transport_consumption": 9e10,
    }
    for household in situation["households"].values():
        household.update({name: {YEAR: value} for name, value in totals.items()})
    sim = Simulation(situation=situation)
    assert calculate(sim, "shareholding") == pytest.approx([7e4 / 1e13] * 2)
    assert calculate(sim, "consumption_shareholding") == pytest.approx(
        [8e3 / 1.9e11] * 2
    )


def test_every_key_component_has_a_uk_total_input():
    from policyengine_uk.system import system
    from policyengine_uk.utils.carbon import CARBON_CATEGORIES
    from policyengine_uk.utils.uk_totals import KEYS, components, total_name

    growth = {
        "corporate_sector_wealth": "per_capita_gdp",
        "consumption": "consumer_price_index",
    }
    for key in KEYS:
        assert components(key) == list(system.get_variable(key).adds)
        for component in components(key):
            variable = system.get_variable(total_name(component))
            assert variable.entity.key == "household"
            assert variable.uprating == (
                f"gov.economic_assumptions.indices.uk_totals.{growth[key]}"
            )
    assert set(CARBON_CATEGORIES) == set(components("consumption"))


# The helper whoever holds the whole population calls.


def test_add_uk_totals_writes_each_components_weighted_total():
    from policyengine_uk.utils.uk_totals import add_uk_totals, uk_total_columns

    carrying = add_uk_totals(population_dataset(POPULATION)).household
    expected = hand_totals(POPULATION)
    assert set(uk_total_columns()) == set(expected)
    for name, value in expected.items():
        # The same total on every household; 0 for a component no household has.
        assert carrying[name].to_numpy() == pytest.approx([value] * len(POPULATION))
    assert expected["uk_total_education_consumption"] == 0


def test_a_region_taken_after_add_uk_totals_gets_its_national_shares():
    """As a regional run filters rows from a dataset that carries the totals."""
    from policyengine_uk.utils.uk_totals import add_uk_totals

    whole = spread_values(population_simulation(POPULATION))
    carrying = add_uk_totals(population_dataset(POPULATION))
    wales = carrying.copy()
    wales.household = wales.household[wales.household.region == "WALES"]
    kept = wales.household.household_id
    wales.person = wales.person[wales.person.person_household_id.isin(kept)]
    wales.benunit = wales.benunit[wales.benunit.benunit_id.isin(kept)]
    values = spread_values(Simulation(dataset=wales, reform=SPREAD_REFORM))
    for variable in SPREAD:
        assert values[variable] == pytest.approx(whole[variable][2:], rel=1e-5), (
            variable
        )


def test_add_uk_totals_gives_each_year_of_a_multi_year_dataset_its_own():
    from policyengine_uk.data import UKMultiYearDataset
    from policyengine_uk.utils.uk_totals import add_uk_totals

    later = [
        {**row, "household_weight": 2 * row["household_weight"]} for row in POPULATION
    ]
    carrying = add_uk_totals(
        UKMultiYearDataset(
            datasets=[
                population_dataset(POPULATION, year=2025),
                population_dataset(later, year=2026),
            ]
        )
    )
    for year, rows in [(2025, POPULATION), (2026, later)]:
        household = carrying[year].household
        assert household["uk_total_corporate_wealth"].iloc[0] == pytest.approx(
            hand_totals(rows)["uk_total_corporate_wealth"]
        )


def test_filter_dataset_extract_keeps_its_national_share():
    """An extract of one household used to take every UK total: its share was
    1 over its own weight."""
    from policyengine_uk.data.filter_dataset import filter_dataset

    whole_sim = population_simulation(POPULATION)
    whole = spread_values(whole_sim)
    extract = filter_dataset(whole_sim, household_id=3, year=YEAR)
    values = spread_values(Simulation(dataset=extract, reform=SPREAD_REFORM))
    for variable in SPREAD:
        assert values[variable] == pytest.approx(whole[variable][2:3], rel=1e-5), (
            variable
        )
