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
