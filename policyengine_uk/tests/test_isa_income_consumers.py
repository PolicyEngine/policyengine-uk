"""ISA income keeps consumer-specific gross and taxable income definitions."""

import pandas as pd
import pytest

from policyengine_uk import Simulation
from policyengine_uk.data.dataset_schema import UKMultiYearDataset, UKSingleYearDataset


pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")


def test_legacy_and_additive_isa_income_reach_the_same_local_ctr_gross_band():
    """Westminster2026:14800/52 exceeds279, so10.60*52=551.20.

    Employment5200 + legacy gross interest9000 + new ISA dividends600.
    The explicit exemption1000 differs from ISA interest500. Normalization
    changes9000 to8000, but cannot remove1000 from the gross CTR band.
    """
    dataset = UKSingleYearDataset(
        person=pd.DataFrame(
            {
                "person_id": [1, 2],
                "person_benunit_id": [1, 2],
                "person_household_id": [1, 1],
                "age": [35, 25],
                "is_household_head": [True, False],
                "employment_income": [0, 5_200],
                "weekly_hours": [0, 16],
                "savings_interest_income": [0, 9_000],
                "individual_savings_account_interest_income": [0, 500],
                "tax_free_savings_income": [0, 1_000],
                "individual_savings_account_dividend_income": [0, 600],
            }
        ),
        benunit=pd.DataFrame({"benunit_id": [1, 2]}),
        household=pd.DataFrame(
            {
                "household_id": [1],
                "household_weight": [1.0],
                "country": ["ENGLAND"],
                "region": ["LONDON"],
                "local_authority": ["WESTMINSTER"],
                "council_tax": [1_800],
            }
        ),
        fiscal_year=2026,
    )
    situation = {
        "people": {
            "claimant": {"age": {2026: 35}, "is_household_head": {2026: True}},
            "non_dep": {
                "age": {2026: 25},
                "is_household_head": {2026: False},
                "employment_income": {2026: 5_200},
                "weekly_hours": {2026: 16},
                "savings_interest_income": {2026: 8_000},
                "individual_savings_account_interest_income": {2026: 500},
                "tax_free_savings_income": {2026: 1_000},
                "individual_savings_account_dividend_income": {2026: 600},
            },
        },
        "benunits": {
            "claimant_benunit": {"members": ["claimant"]},
            "non_dep_benunit": {"members": ["non_dep"]},
        },
        "households": {
            "household": {
                "members": ["claimant", "non_dep"],
                "country": {2026: "ENGLAND"},
                "local_authority": {2026: "WESTMINSTER"},
                "council_tax": {2026: 1_800},
            }
        },
    }
    legacy = Simulation(dataset=UKMultiYearDataset(datasets=[dataset]))
    additive = Simulation(situation=situation)
    for simulation in (legacy, additive):
        assert simulation.calculate(
            "council_tax_reduction_individual_non_dep_deduction_eligible", 2026
        ).tolist() == [False, True]
        assert simulation.calculate(
            "westminster_council_tax_reduction_individual_non_dep_deduction", 2026
        ).tolist() == pytest.approx([0, 551.20], abs=0.01)
