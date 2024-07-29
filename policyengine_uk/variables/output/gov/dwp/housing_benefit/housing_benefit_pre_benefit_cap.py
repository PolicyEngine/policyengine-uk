from policyengine_uk.model_api import *


class housing_benefit_pre_benefit_cap(Variable):
    value_type = float
    entity = BenUnit
    label = "Housing Benefit pre-benefit cap"
    definition_period = YEAR
    unit = GBP
    defined_for = "housing_benefit_eligible"

    adds = ["housing_benefit_entitlement"]
