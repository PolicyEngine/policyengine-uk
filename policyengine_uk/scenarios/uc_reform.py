from policyengine_uk.model_api import Scenario
from policyengine_uk import Microsimulation
from policyengine_uk.variables.gov.dwp.universal_credit.standard_allowance.uc_standard_allowance_claimant_type import (
    UCClaimantType,
)
import numpy as np


BASELINE_UC_REBALANCING_YEAR = 2025


def _cpi_protected_uc_award_monthly(
    sim: Microsimulation, year: int, claimant_type: str
) -> float:
    parameters = sim.tax_benefit_system.parameters
    baseline = parameters(str(BASELINE_UC_REBALANCING_YEAR))
    current = parameters(str(year))
    cpi_factor = float(current.gov.benefit_uprating_cpi) / float(
        baseline.gov.benefit_uprating_cpi
    )
    baseline_standard_allowance = float(
        baseline.gov.dwp.universal_credit.standard_allowance.amount[claimant_type]
    )
    baseline_health_element = float(
        baseline.gov.dwp.universal_credit.elements.disabled.amount
    )
    return (baseline_standard_allowance + baseline_health_element) * cpi_factor


def _rebalanced_standard_allowance_monthly(
    sim: Microsimulation, year: int, claimant_type: str
) -> float:
    current = sim.tax_benefit_system.parameters(str(year))
    standard_allowance = float(
        current.gov.dwp.universal_credit.standard_allowance.amount[claimant_type]
    )
    uplift = float(
        current.gov.dwp.universal_credit.rebalancing.standard_allowance_uplift
    )
    return standard_allowance * (1 + uplift)


def _protected_existing_health_element_monthly(
    sim: Microsimulation, year: int
) -> float:
    return _cpi_protected_uc_award_monthly(
        sim, year, "SINGLE_OLD"
    ) - _rebalanced_standard_allowance_monthly(sim, year, "SINGLE_OLD")


def _single_young_standard_allowance_topup_monthly(
    sim: Microsimulation, year: int
) -> float:
    protected_young_award = _cpi_protected_uc_award_monthly(sim, year, "SINGLE_YOUNG")
    standard_allowance = _rebalanced_standard_allowance_monthly(
        sim, year, "SINGLE_YOUNG"
    )
    protected_health_element = _protected_existing_health_element_monthly(sim, year)
    return max(
        0.0, protected_young_award - standard_allowance - protected_health_element
    )


def add_universal_credit_reform(sim: Microsimulation):
    rebalancing = sim.tax_benefit_system.parameters.gov.dwp.universal_credit.rebalancing

    generator = np.random.default_rng(43)

    uc_seed = generator.random(len(sim.calculate("benunit_id")))
    post_2025_claimant_share = {
        2025: 0,
        2026: 0.11,
        2027: 0.13,
        2028: 0.16,
        2029: 0.22,
    }  # WPI Economics for Trussell Trust based on admin PIP data, 2025
    new_claimant_health_element = rebalancing.new_claimant_health_element
    for year in range(2026, 2030):
        if not rebalancing.active(year):
            continue
        is_post_2025_claimant = uc_seed < post_2025_claimant_share[year]

        claimant_type = sim.calculate("uc_standard_allowance_claimant_type", year)
        current_standard_allowance = sim.calculate("uc_standard_allowance", year)
        single_young_topup = (
            _single_young_standard_allowance_topup_monthly(sim, year) * 12
        )
        current_standard_allowance[
            claimant_type == UCClaimantType.SINGLE_YOUNG.name
        ] += single_young_topup
        sim.set_input("uc_standard_allowance", year, current_standard_allowance)

        current_health_element = sim.calculate("uc_LCWRA_element", year)
        has_health_element = current_health_element > 0
        protected_health_element = (
            _protected_existing_health_element_monthly(sim, year) * 12
        )
        current_health_element[has_health_element & ~is_post_2025_claimant] = (
            protected_health_element
        )
        # Set post-April 2026 claimants to £217.26/month.
        # https://bills.parliament.uk/publications/62123/documents/6889#page=16
        current_health_element[has_health_element & is_post_2025_claimant] = (
            new_claimant_health_element(year) * 12
        )  # Monthly amount * 12
        sim.set_input("uc_LCWRA_element", year, current_health_element)

    # Standard allowance uplift is handled in the formula itself so user
    # reforms to the base amount are applied before the uplift.


universal_credit_july_2025_reform = Scenario(
    simulation_modifier=add_universal_credit_reform,
)
