from policyengine_uk.model_api import Scenario
from policyengine_uk import Microsimulation
import numpy as np


def add_universal_credit_reform(sim: Microsimulation):
    rebalancing = (
        sim.tax_benefit_system.parameters.gov.dwp.universal_credit.rebalancing
    )

    uc_seed = np.random.random(len(sim.calculate("benunit_id")))
    p_uc_post_2026_status = {
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
        is_post_25_claimant = uc_seed < p_uc_post_2026_status[year]
        current_health_element = sim.calculate("uc_LCWRA_element", year)
        # Set new claimants to £217.26/month from April 2026 (pre-2026 claimaints keep inflation-linked increases)
        # https://bills.parliament.uk/publications/62123/documents/6889#page=16
        current_health_element[
            (current_health_element > 0) & is_post_25_claimant
        ] = (
            new_claimant_health_element(year) * 12
        )  # Monthly amount * 12
        sim.set_input("uc_LCWRA_element", year, current_health_element)

    # https://bills.parliament.uk/publications/62123/documents/6889#page=14

    uc_uplift = rebalancing.standard_allowance_uplift

    for year in range(2026, 2030):
        if not rebalancing.active(year):
            continue
        previous_value = sim.calculate("uc_standard_allowance", year - 1)
        new_value = previous_value * (1 + uc_uplift(year))
        sim.set_input("uc_standard_allowance", year, new_value)


universal_credit_july_2025_reform = Scenario(
    simulation_modifier=add_universal_credit_reform,
)
