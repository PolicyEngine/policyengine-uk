"""Housing Benefit take-up with the accommodation status in data-built runs.

A hand-entered family with in_specified_or_temporary_accommodation claims
Housing Benefit (would_claim_housing_benefit). A simulation built from data
keeps its reporters-only rule: the status doesn't make a family claim, so a
data-built family with the status and no Housing Benefit report gets no help
with the rent. No dataset sets the status, so this pins the data branch
without survey data.
"""

import pandas as pd
import pytest

from policyengine_uk import Microsimulation, Simulation
from policyengine_uk.data import UKMultiYearDataset, UKSingleYearDataset
from policyengine_uk.utils.data_source import built_from_data

YEAR = 2026
RENT = 10_000


def dataset(housing_benefit_reported):
    return UKMultiYearDataset(
        datasets=[
            UKSingleYearDataset(
                person=pd.DataFrame(
                    {
                        "person_id": [1],
                        "person_benunit_id": [1],
                        "person_household_id": [1],
                        "age": [40],
                        "housing_benefit_reported": [housing_benefit_reported],
                    }
                ),
                benunit=pd.DataFrame(
                    {
                        "benunit_id": [1],
                        "in_specified_or_temporary_accommodation": [True],
                        "would_claim_uc": [True],
                    }
                ),
                household=pd.DataFrame(
                    {
                        "household_id": [1],
                        "region": ["LONDON"],
                        "tenure_type": ["RENT_FROM_COUNCIL"],
                        "rent": [RENT],
                        "council_tax": [1_500],
                    }
                ),
                fiscal_year=YEAR,
            )
        ]
    )


SITUATION = {
    "people": {
        "claimant": {
            "age": {YEAR: 40},
            "housing_benefit_reported": {YEAR: 0},
        }
    },
    "benunits": {
        "benunit": {
            "members": ["claimant"],
            "in_specified_or_temporary_accommodation": {YEAR: True},
            "would_claim_uc": {YEAR: True},
            "claims_all_entitled_benefits": {YEAR: False},
        }
    },
    "households": {
        "household": {
            "members": ["claimant"],
            "region": {YEAR: "LONDON"},
            "tenure_type": {YEAR: "RENT_FROM_COUNCIL"},
            "rent": {YEAR: RENT},
            "council_tax": {YEAR: 1_500},
        }
    },
}


@pytest.mark.parametrize("simulation_class", [Simulation, Microsimulation])
def test_data_built_family_with_the_status_and_no_report_does_not_claim(
    simulation_class,
):
    simulation = simulation_class(dataset=dataset(housing_benefit_reported=0))
    assert built_from_data(simulation)
    assert not simulation.calculate("would_claim_housing_benefit", YEAR)[0]
    # The family can claim, but doesn't, and Universal Credit leaves the rent
    # out, so nothing pays it.
    assert simulation.calculate("housing_benefit_eligible", YEAR)[0]
    assert simulation.calculate("housing_benefit", YEAR)[0] == 0
    assert simulation.calculate("uc_housing_costs_element", YEAR)[0] == 0


@pytest.mark.parametrize("simulation_class", [Simulation, Microsimulation])
def test_data_built_family_with_the_status_and_a_report_claims(simulation_class):
    simulation = simulation_class(dataset=dataset(housing_benefit_reported=5_000))
    assert simulation.calculate("would_claim_housing_benefit", YEAR)[0]
    # Universal Credit passports the Housing Benefit means test, so Housing
    # Benefit pays the whole rent.
    assert simulation.calculate("housing_benefit", YEAR)[0] == pytest.approx(
        RENT, abs=0.01
    )


def test_the_same_family_hand_entered_claims():
    simulation = Simulation(situation=SITUATION)
    assert not built_from_data(simulation)
    assert simulation.calculate("would_claim_housing_benefit", YEAR)[0]
    assert simulation.calculate("housing_benefit", YEAR)[0] == pytest.approx(
        RENT, abs=0.01
    )
