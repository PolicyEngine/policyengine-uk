from policyengine_uk.model_api import *


class uc_receives_new_claimant_health_element(Variable):
    value_type = bool
    entity = BenUnit
    label = "Universal Credit LCWRA element at the new-claimant rate"
    documentation = (
        "Whether the award's LCWRA element is paid at the rate for claimants "
        "other than a pre-2026 claimant, a severe conditions criteria claimant "
        "or a claimant who is terminally ill (UC Regs 2013 reg. 36, from 6 "
        "April 2026). False pays the protected LCWRA amount. A household "
        "situation can set it; otherwise it is false. Simulations built from "
        "data that do not supply it assign it by a seeded draw at the share of "
        "health-element claimants expected to be new claimants each year."
    )
    definition_period = YEAR
    default_value = False
    reference = "https://www.legislation.gov.uk/uksi/2013/376/regulation/36"
