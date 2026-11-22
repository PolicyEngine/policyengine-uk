"""The firm entity leaves household results alone.

Firm-side rules are built but not wired into any household tax or benefit.
These tests check that structurally (no firm variable is a term of
gov_tax or of the household budget totals) and live: for a varied set of
household situations, adding firms to the situation, or reforming
firm-only rules, leaves every household and government total exactly as
it was. (Before review, a frozen fixture also matched the base commit
70014b3 exactly; it was dropped so later changes to household rules do
not break this test.)
"""

import numpy as np
import pytest

YEARS = (2025, 2026)

HOUSEHOLD_VARIABLES = (
    "gov_tax",
    "household_tax",
    "household_net_income",
    "gov_balance",
    "household_benefits",
)

# A firm-only reform: raise the corporation tax main rate and cut the
# Employment Allowance.
FIRM_REFORM = {
    "gov.hmrc.corporation_tax.main_rate": {"2020-01-01.2035-12-31": 0.3},
    "gov.hmrc.national_insurance.employment_allowance.amount": {
        "2020-01-01.2035-12-31": 1_000
    },
}

FIRMS = {
    "manufacturer": {
        "firm_employees": 20,
        "firm_paybill": 700_000,
        "firm_taxable_trading_profit": 400_000,
        "firm_rateable_value": 60_000,
        "firm_standard_rated_supplies": 2_000_000,
        "firm_input_vat": 150_000,
    },
    "shop": {
        "firm_legal_form": "SOLE_TRADER",
        "firm_employees": 2,
        "firm_paybill": 50_000,
        "firm_taxable_trading_profit": 70_000,
    },
}


def _household(members, **household_inputs):
    return {"members": list(members), **household_inputs}


def situations(year: int) -> dict:
    """Varied single-household situations for ``year``."""

    def person(age, **incomes):
        return {"age": {year: age}, **{k: {year: v} for k, v in incomes.items()}}

    def single(name, region="LONDON", household=None, **person_inputs):
        return {
            "people": {name: person(**person_inputs)},
            "benunits": {"benunit": {"members": [name]}},
            "households": {
                "household": _household(
                    [name], region={year: region}, **(household or {})
                )
            },
        }

    couple_members = ["parent1", "parent2", "child1", "child2"]
    return {
        "single_earner": single(
            "adult", region="NORTH_WEST", age=35, employment_income=32_000
        ),
        "couple_with_children_on_uc": {
            "people": {
                "parent1": person(34, employment_income=14_000),
                "parent2": person(32),
                "child1": person(7),
                "child2": person(3),
            },
            "benunits": {
                "benunit": {"members": couple_members, "would_claim_uc": {year: True}}
            },
            "households": {
                "household": _household(
                    couple_members,
                    region={year: "WEST_MIDLANDS"},
                    rent={year: 9_600},
                    tenure_type={year: "RENT_PRIVATELY"},
                )
            },
        },
        "pensioner": single(
            "pensioner",
            region="SOUTH_WEST",
            age=72,
            state_pension=11_500,
            private_pension_income=6_000,
            savings_interest_income=1_200,
        ),
        "self_employed": single(
            "trader", region="EAST_MIDLANDS", age=45, self_employment_income=48_000
        ),
        "high_earner_with_dividends": single(
            "director",
            region="SOUTH_EAST",
            age=52,
            employment_income=160_000,
            dividend_income=40_000,
            property_income=12_000,
        ),
        "renter_in_scotland": single(
            "renter",
            region="SCOTLAND",
            household={
                "rent": {year: 7_800},
                "tenure_type": {year: "RENT_PRIVATELY"},
                "council_tax": {year: 1_400},
                "full_rate_vat_consumption": {year: 9_000},
                "reduced_rate_vat_consumption": {year: 600},
            },
            age=28,
            employment_income=27_500,
        ),
        "low_paid_lone_parent_wales": {
            "people": {
                "parent": person(29, employment_income=11_000),
                "child": person(4),
            },
            "benunits": {
                "benunit": {
                    "members": ["parent", "child"],
                    "would_claim_uc": {year: True},
                }
            },
            "households": {
                "household": _household(
                    ["parent", "child"],
                    region={year: "WALES"},
                    rent={year: 6_000},
                    tenure_type={year: "RENT_FROM_COUNCIL"},
                )
            },
        },
        "two_earner_couple_london": {
            "people": {
                "a": person(41, employment_income=55_000),
                "b": person(39, employment_income=38_000, self_employment_income=6_000),
            },
            "benunits": {"benunit": {"members": ["a", "b"]}},
            "households": {
                "household": _household(
                    ["a", "b"],
                    region={year: "LONDON"},
                    tenure_type={year: "OWNED_WITH_MORTGAGE"},
                    council_tax={year: 2_100},
                    full_rate_vat_consumption={year: 21_000},
                    petrol_spending={year: 1_500},
                )
            },
        },
    }


def _values(simulation, variables, year) -> dict:
    return {
        name: [
            float(value)
            for value in np.asarray(simulation.calculate(name, year), dtype=float)
        ]
        for name in variables
    }


def _values(simulation, variables, year) -> dict:
    return {
        name: np.asarray(simulation.calculate(name, year), dtype=float)
        for name in variables
    }


CASES = sorted((name, year) for year in YEARS for name in situations(year))


def test_no_firm_variable_is_a_term_of_gov_tax():
    from policyengine_uk import CountryTaxBenefitSystem
    from policyengine_uk.variables.gov.gov_tax import GOV_TAX_VARIABLES

    system = CountryTaxBenefitSystem()
    assert [
        name
        for name in GOV_TAX_VARIABLES
        if system.variables[name].entity.key == "firm"
    ] == []


def test_no_firm_variable_is_a_budget_term():
    from policyengine_uk import CountryTaxBenefitSystem
    from policyengine_uk.programs import budget_programs

    system = CountryTaxBenefitSystem()
    assert [
        term.variable
        for term in budget_programs()
        if term.variable in system.variables
        and system.variables[term.variable].entity.key == "firm"
    ] == []


@pytest.mark.parametrize("name,year", CASES)
def test_firms_in_a_situation_leave_household_results_unchanged(name, year):
    from policyengine_uk import Simulation
    from policyengine_uk.variables.gov.gov_tax import GOV_TAX_VARIABLES

    situation = situations(year)[name]
    variables = HOUSEHOLD_VARIABLES + tuple(GOV_TAX_VARIABLES)
    without = _values(Simulation(situation=situation), variables, year)
    with_firms = Simulation(situation={**situation, "firms": FIRMS})
    assert np.asarray(with_firms.calculate("firm_tax", year)).sum() > 0
    actual = _values(with_firms, variables, year)
    mismatches = {
        variable: (without[variable], actual[variable])
        for variable in variables
        if not np.array_equal(without[variable], actual[variable])
    }
    assert not mismatches, mismatches


@pytest.mark.parametrize("name,year", CASES)
def test_firm_only_reform_leaves_household_results_unchanged(name, year):
    from policyengine_uk import Simulation
    from policyengine_uk.variables.gov.gov_tax import GOV_TAX_VARIABLES

    situation = {**situations(year)[name], "firms": FIRMS}
    baseline = Simulation(situation=situation)
    reformed = Simulation(situation=situation, reform=FIRM_REFORM)
    # The reform must move the firms, or it proves nothing.
    assert (
        np.asarray(reformed.calculate("firm_tax", year)).sum()
        > np.asarray(baseline.calculate("firm_tax", year)).sum()
    )
    variables = HOUSEHOLD_VARIABLES + tuple(GOV_TAX_VARIABLES)
    expected = _values(baseline, variables, year)
    actual = _values(reformed, variables, year)
    mismatches = {
        variable: (expected[variable], actual[variable])
        for variable in variables
        if not np.array_equal(expected[variable], actual[variable])
    }
    assert not mismatches, mismatches
