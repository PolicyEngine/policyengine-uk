import pandas as pd
import pytest

from policyengine_uk import Simulation
from policyengine_uk.data.dataset_schema import UKSingleYearDataset
from policyengine_uk.data.economic_assumptions import extend_single_year_dataset
from policyengine_uk.system import system

LIFETIME_ISA_HOLDER = {
    "people": {
        "person": {
            "age": {"2025": 30},
            "lifetime_isa_balance": {"2025": 10_000},
        }
    },
    "benunits": {"benunit": {"members": ["person"]}},
    "households": {"household": {"members": ["person"], "savings": {"2025": 1_000}}},
}


def test_lifetime_isa_balances_uprate_with_the_other_financial_stocks():
    # Datasets store the person balances and their household sum; both must
    # move with savings, or the stored household total drifts from its parts.
    dataset = UKSingleYearDataset(
        person=pd.DataFrame(
            {
                "person_id": [1, 2],
                "person_benunit_id": [1, 1],
                "person_household_id": [1, 1],
                "age": [30, 28],
                "lifetime_isa_balance": [4_000.0, 6_000.0],
            }
        ),
        benunit=pd.DataFrame({"benunit_id": [1]}),
        household=pd.DataFrame(
            {
                "household_id": [1],
                "region": ["LONDON"],
                "tenure_type": ["RENT_PRIVATELY"],
                "council_tax": [1_500.0],
                "rent": [12_000.0],
                "household_weight": [1.0],
                "savings": [1_000.0],
                "household_lifetime_isa_balance": [10_000.0],
            }
        ),
        fiscal_year=2025,
    )

    extended = extend_single_year_dataset(
        dataset,
        tax_benefit_system_parameters=system.parameters,
        end_year=2027,
    )

    for year in (2026, 2027):
        growth = extended[year].household["savings"].iloc[0] / 1_000.0
        assert growth != pytest.approx(1.0)
        person = extended[year].person["lifetime_isa_balance"]
        household = extended[year].household["household_lifetime_isa_balance"]
        assert list(person) == pytest.approx([4_000.0 * growth, 6_000.0 * growth])
        assert household.iloc[0] == pytest.approx(person.sum())


def test_emptying_a_person_sources_list_disregards_the_lifetime_isa_there_only():
    # The Treasury Committee's proposal to disregard Lifetime ISAs in Universal
    # Credit is a change to one list; the other means tests keep counting them.
    reform = {
        "gov.dwp.universal_credit.means_test.capital.person_sources": {
            "2025-01-01.2100-12-31": []
        }
    }
    baseline = Simulation(situation=LIFETIME_ISA_HOLDER)
    reformed = Simulation(situation=LIFETIME_ISA_HOLDER, reform=reform)

    assert baseline.calculate("uc_assessable_capital", 2025)[0] == 8_500
    assert reformed.calculate("uc_assessable_capital", 2025)[0] == 1_000
    assert reformed.calculate("housing_benefit_assessable_capital", 2025)[0] == 8_500


def test_lifetime_isa_capital_is_not_prorated_monthly():
    simulation = Simulation(situation=LIFETIME_ISA_HOLDER)

    assert simulation.calculate("lifetime_isa_balance", "2025-06")[0] == 10_000
    assert simulation.calculate("lifetime_isa_countable_capital", "2025-06")[0] == 7_500
    assert simulation.calculate("uc_assessable_capital", "2025-06")[0] == 8_500
