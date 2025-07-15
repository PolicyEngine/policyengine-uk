from policyengine_uk.model_api import *


class child_benefit_entitlement(Variable):
    label = "CB entitlement"
    entity = ben_unit
    definition_period = YEAR
    value_type = float
    unit = GBP

    adds = ["child_benefit_respective_amount"]
