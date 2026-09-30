from policyengine_uk.model_api import Scenario
from policyengine_uk import Microsimulation
from policyengine_uk.variables.gov.dwp.universal_credit.standard_allowance.uc_standard_allowance_claimant_type import (
    UCClaimantType,
)
import numpy as np

MONTHS_IN_YEAR = 12


BASELINE_UC_REBALANCING_YEAR = 2025
FIRST_REBALANCING_YEAR = 2026
# Universal Credit Act 2025 ss3-4 freeze and protect the LCWRA element for
# 2026-27 to 2029-30; section 150 uprating of both LCWRA amounts resumes from
# 2030-31.
LAST_PROTECTED_YEAR = 2029
# Fiscal-year parameter values run to 2040.
LAST_MODELLED_YEAR = 2040
# Share of LCWRA claimants who claimed after April 2026 (WPI Economics for
# Trussell Trust, from admin PIP data, 2025). Held at the 2029-30 share after
# that, the last year the source covers.
POST_2025_CLAIMANT_SHARE = {
    2025: 0,
    2026: 0.11,
    2027: 0.13,
    2028: 0.16,
    2029: 0.22,
}
CLAIMANT_TYPES = [claimant_type.name for claimant_type in UCClaimantType]


def _benefit_uprating_ratio(
    sim: Microsimulation, year: int, base_year: int = BASELINE_UC_REBALANCING_YEAR
) -> float:
    parameters = sim.tax_benefit_system.parameters
    current_index = float(parameters(str(year)).gov.benefit_uprating_cpi)
    baseline_index = float(parameters(str(base_year)).gov.benefit_uprating_cpi)
    return current_index / baseline_index


def _rebalanced_standard_allowance_monthly(
    sim: Microsimulation, year: int, claimant_type: str
) -> float:
    current = sim.tax_benefit_system.parameters(str(year))
    return float(
        current.gov.dwp.universal_credit.standard_allowance.amount[claimant_type]
    )


def _protected_existing_health_element_monthly(
    sim: Microsimulation, year: int
) -> float:
    """The protected LCWRA amount for pre-2026, severe conditions and
    terminally ill claimants (Universal Credit Act 2025 ss2-4).

    s3 freezes the amount (it cannot fall) and s4(2) raises it where needed
    so that, for every amount of the standard allowance, standard allowance
    plus LCWRA is at least the previous year's sum raised by September CPI.
    Regulation 36 has one protected amount, so it is the highest amount any
    standard allowance needs. From 2030-31 section 150 uprates it again.
    """
    if year > LAST_PROTECTED_YEAR:
        return _protected_existing_health_element_monthly(
            sim, LAST_PROTECTED_YEAR
        ) * _benefit_uprating_ratio(sim, year, LAST_PROTECTED_YEAR)
    parameters = sim.tax_benefit_system.parameters
    protected = float(
        parameters(
            str(BASELINE_UC_REBALANCING_YEAR)
        ).gov.dwp.universal_credit.elements.disabled.amount
    )
    for current in range(FIRST_REBALANCING_YEAR, year + 1):
        growth = _benefit_uprating_ratio(sim, current, current - 1)
        required = max(
            (
                _rebalanced_standard_allowance_monthly(sim, current - 1, claimant_type)
                + protected
            )
            * growth
            - _rebalanced_standard_allowance_monthly(sim, current, claimant_type)
            for claimant_type in CLAIMANT_TYPES
        )
        protected = max(protected, required)
    return protected


def add_universal_credit_reform(sim: Microsimulation):
    rebalancing = sim.tax_benefit_system.parameters.gov.dwp.universal_credit.rebalancing

    generator = np.random.default_rng(43)

    uc_seed = generator.random(len(sim.calculate("benunit_id")))
    new_claimant_health_element = rebalancing.new_claimant_health_element
    for year in range(FIRST_REBALANCING_YEAR, LAST_MODELLED_YEAR + 1):
        if not rebalancing.active(year):
            continue
        share = POST_2025_CLAIMANT_SHARE[min(year, LAST_PROTECTED_YEAR)]
        is_post_2025_claimant = uc_seed < share
        current_health_element = sim.calculate("uc_LCWRA_element", year)
        has_health_element = current_health_element > 0
        protected = has_health_element & ~is_post_2025_claimant
        current_health_element[protected] = (
            _protected_existing_health_element_monthly(sim, year) * MONTHS_IN_YEAR
        )
        # Post-April 2026 claimants get the new-claimant amount (£217.26 a
        # month from April 2026, frozen to 2029-30 by s3).
        # https://www.legislation.gov.uk/ukpga/2025/22/section/2
        current_health_element[has_health_element & is_post_2025_claimant] = (
            new_claimant_health_element(year) * MONTHS_IN_YEAR
        )
        sim.set_input("uc_LCWRA_element", year, current_health_element)

    # The standard allowance uplift is applied through the standard
    # allowance's uprating index (standard_allowance/create_uprating_index.py).


universal_credit_july_2025_reform = Scenario(
    simulation_modifier=add_universal_credit_reform,
)
