from policyengine_uk.model_api import *


class uc_new_claimant_health_element_draw(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit new-claimant health element draw"
    documentation = (
        "A uniform in [0, 1) that the dataset build assigns to each benefit "
        "unit and stores. It is an allocation device, not an observed fact: "
        "in each Universal Credit rebalancing year, a simulation built from "
        "data that supplies no new-claimant status for the year gives a "
        "benefit unit the new-claimant LCWRA rate when this draw falls below "
        "gov.dwp.universal_credit.rebalancing.new_claimant_share. Its "
        "situation default, 1.0, falls below no share. A dataset without "
        "the column keeps the model's own seeded draw."
    )
    definition_period = YEAR
    default_value = 1.0
