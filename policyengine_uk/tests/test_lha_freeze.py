"""Regression tests for the LHA freeze parameter."""

from policyengine_uk import Simulation


YEAR = 2026

SITUATION = {
    "people": {
        "person": {
            "age": {YEAR: 30},
            "employment_income": {YEAR: 0},
        }
    },
    "benunits": {
        "benunit": {
            "members": ["person"],
            "benunit_rent": {YEAR: 10_000},
            "LHA_eligible": {YEAR: True},
            "housing_benefit_applicable_amount": {YEAR: 11_000},
            "housing_benefit_applicable_income": {YEAR: 11_000},
            "housing_benefit_non_dep_deductions": {YEAR: 0},
        }
    },
    "households": {
        "household": {
            "members": ["person"],
            "region": {YEAR: "LONDON"},
        }
    },
}


def test_lha_freeze_changes_lha_rate_and_housing_benefit_entitlement():
    frozen = Simulation(
        situation=SITUATION,
        reform={"gov.dwp.LHA.freeze": {"2026": True}},
    )
    unfrozen = Simulation(
        situation=SITUATION,
        reform={"gov.dwp.LHA.freeze": {"2026": False}},
    )

    frozen_rate = frozen.calculate("BRMA_LHA_rate", YEAR)[0]
    unfrozen_rate = unfrozen.calculate("BRMA_LHA_rate", YEAR)[0]
    frozen_entitlement = frozen.calculate("housing_benefit_entitlement", YEAR)[0]
    unfrozen_entitlement = unfrozen.calculate("housing_benefit_entitlement", YEAR)[0]

    assert unfrozen_rate > frozen_rate
    assert unfrozen_entitlement > frozen_entitlement
