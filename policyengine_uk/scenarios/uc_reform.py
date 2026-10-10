from policyengine_uk.model_api import Scenario
from policyengine_uk import Microsimulation
import numpy as np


# The standard allowance amounts the protected LCWRA amount is paired with in
# the Universal Credit Act 2025 s. 4(2) duty: every amount of the allowance.
STANDARD_ALLOWANCE_TYPES = (
    "SINGLE_YOUNG",
    "SINGLE_OLD",
    "COUPLE_YOUNG",
    "COUPLE_OLD",
)


def protected_lcwra_floor(
    previous_amount: float,
    previous_standard_allowances: dict,
    standard_allowances: dict,
    cpi_factor: float,
) -> float:
    """The lowest protected LCWRA amount the Universal Credit Act 2025 allows.

    s. 4(2): for each standard allowance amount, the protected LCWRA amount
    plus that allowance must be at least the previous tax year's sum,
    increased by the relevant CPI percentage (never below 0%, s. 4(4)(a)). s. 3
    switches off the element's ordinary uprating, so the amount otherwise stays
    where it was. All amounts are monthly.
    """
    factor = max(float(cpi_factor), 1.0)
    required = max(
        (previous_amount + previous_standard_allowances[claimant_type]) * factor
        - standard_allowances[claimant_type]
        for claimant_type in STANDARD_ALLOWANCE_TYPES
    )
    return max(float(previous_amount), required)


def _standard_allowances_monthly(sim: Microsimulation, year: int) -> dict:
    amounts = sim.tax_benefit_system.parameters(
        str(year)
    ).gov.dwp.universal_credit.standard_allowance.amount
    return {
        claimant_type: float(amounts[claimant_type])
        for claimant_type in STANDARD_ALLOWANCE_TYPES
    }


def _relevant_cpi_factor(sim: Microsimulation, year: int) -> float:
    """1 + the relevant CPI percentage for a tax year (UC Act 2025 s. 4(4)(a)):
    the CPI 12-month rate in the September before it. The 0% floor is applied
    in :func:`protected_lcwra_floor`."""
    inputs = sim.tax_benefit_system.parameters.gov.economic_assumptions.statutory_uprating_inputs
    return 1 + float(inputs.cpi_september(f"{year - 1}-09-01"))


# The date the fiscal-year annualisation samples a parameter at
# (policyengine_uk.utils.parameters).
FISCAL_YEAR_SAMPLE_DATE = "04-30"


def _protected_amount_parameter(sim: Microsimulation):
    return sim.tax_benefit_system.parameters.gov.dwp.universal_credit.rebalancing.protected_health_element


def _protected_existing_health_element_monthly(
    sim: Microsimulation, year: int
) -> float:
    """The protected LCWRA amount for a tax year, monthly.

    UC Regs 2013 reg. 36 gives one amount to every pre-2026, severe conditions
    criteria or terminally ill claimant, whatever their age or couple status
    (£429.80 for 2026-27, SI 2026/113 reg. 3(3)(b)). A tax year whose amount is
    null (not yet legislated) takes the s. 4 floor from the year before; any
    other amount, legislated or set by a reform, is used as given.
    """
    parameter = _protected_amount_parameter(sim)
    amount = parameter(f"{year}-{FISCAL_YEAR_SAMPLE_DATE}")
    if amount is not None:
        return float(amount)
    first = min(
        int(entry.instant_str[:4])
        for entry in parameter.values_list
        if entry.value is not None
    )
    if year <= first:
        raise ValueError(
            f"No protected LCWRA amount is set for {year} or any earlier year."
        )
    return protected_lcwra_floor(
        _protected_existing_health_element_monthly(sim, year - 1),
        _standard_allowances_monthly(sim, year - 1),
        _standard_allowances_monthly(sim, year),
        _relevant_cpi_factor(sim, year),
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
        # Copy: calculate returns the simulation's cached array, and the writes
        # below must reach the cache only through set_input.
        current_health_element = np.array(sim.calculate("uc_LCWRA_element", year))
        has_health_element = current_health_element > 0
        # One protected amount for every pre-2026 claimant (reg. 36).
        current_health_element[has_health_element & ~is_post_2025_claimant] = (
            _protected_existing_health_element_monthly(sim, year) * 12
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
