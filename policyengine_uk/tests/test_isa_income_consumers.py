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


@pytest.mark.parametrize("benefit", ["housing_benefit", "esa_income"])
def test_cash_isa_reaches_legacy_awards_like_ordinary_savings(benefit):
    """Cash ISAs count like equal ordinary cash, including the final award.

    These are ongoing public synthetic claims in 2025. ESA is a reported
    award passed through the existing bounded screen, not full entitlement.
    GBP8000 gives eight GBP250 tariff steps above6000, or GBP416 a year.
    """

    def build(savings, cash_isa):
        person = {"age": {2025: 40}}
        household = {
            "members": ["person"],
            "savings": {2025: savings},
            "cash_isa": {2025: cash_isa},
        }
        if benefit == "housing_benefit":
            person.update(
                employment_income={2025: 10_000}, housing_benefit_reported={2025: 1_000}
            )
            household.update(
                tenure_type={2025: "RENT_FROM_COUNCIL"}, rent={2025: 6_000}
            )
        else:
            person.update(esa_income_reported={2025: 1_000}, weekly_hours={2025: 0})
        return Simulation(
            situation={
                "people": {"person": person},
                "benunits": {
                    "benunit": {"members": ["person"], "would_claim_uc": {2025: False}}
                },
                "households": {"household": household},
            }
        )

    lower = build(5_000, 0)
    wrapped = build(5_000, 3_000)
    ordinary = build(8_000, 0)
    awards = [
        float(sim.calculate(benefit, 2025)[0]) for sim in (lower, wrapped, ordinary)
    ]
    assert all(award > 0 for award in awards)
    assert awards[1] == pytest.approx(awards[2], abs=0.01)
    assert awards[1] < awards[0]
    for sim in (wrapped, ordinary):
        assert sim.calculate(f"{benefit}_assessable_capital", 2025).tolist() == [8_000]
        assert sim.calculate(f"{benefit}_tariff_income", 2025).tolist() == [416]
