from policyengine_uk.model_api import Scenario
from policyengine_uk import Microsimulation
from policyengine_uk.variables.gov.dwp.universal_credit.standard_allowance.uc_standard_allowance_claimant_type import (
    UCClaimantType,
)
import numpy as np


BASELINE_UC_REBALANCING_YEAR = 2025


def _benefit_uprating_ratio(sim: Microsimulation, year: int) -> float:
    parameters = sim.tax_benefit_system.parameters
    current_index = float(parameters(str(year)).gov.benefit_uprating_cpi)
    baseline_index = float(
        parameters(str(BASELINE_UC_REBALANCING_YEAR)).gov.benefit_uprating_cpi
    )
    return current_index / baseline_index


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
    baseline = sim.tax_benefit_system.parameters(str(BASELINE_UC_REBALANCING_YEAR))
    protected_combined_award = _benefit_uprating_ratio(sim, year) * (
        float(baseline.gov.dwp.universal_credit.standard_allowance.amount.SINGLE_OLD)
        + float(baseline.gov.dwp.universal_credit.elements.disabled.amount)
    )
    return protected_combined_award - _rebalanced_standard_allowance_monthly(
        sim, year, "SINGLE_OLD"
    )


def _protected_single_young_health_element_monthly(
    sim: Microsimulation, year: int
) -> float:
    baseline = sim.tax_benefit_system.parameters(str(BASELINE_UC_REBALANCING_YEAR))
    protected_combined_award = _benefit_uprating_ratio(sim, year) * (
        float(baseline.gov.dwp.universal_credit.standard_allowance.amount.SINGLE_YOUNG)
        + float(baseline.gov.dwp.universal_credit.elements.disabled.amount)
    )
    return protected_combined_award - _rebalanced_standard_allowance_monthly(
        sim, year, "SINGLE_YOUNG"
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
        current_health_element = sim.calculate("uc_LCWRA_element", year)
        claimant_type = sim.calculate("uc_standard_allowance_claimant_type", year)
        has_health_element = current_health_element > 0
        protected_health_element = np.full(
            current_health_element.shape,
            _protected_existing_health_element_monthly(sim, year) * 12,
            dtype=current_health_element.dtype,
        )
        protected_health_element[claimant_type == UCClaimantType.SINGLE_YOUNG.name] = (
            _protected_single_young_health_element_monthly(sim, year) * 12
        )
        current_health_element[has_health_element & ~is_post_2025_claimant] = (
            protected_health_element[has_health_element & ~is_post_2025_claimant]
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
