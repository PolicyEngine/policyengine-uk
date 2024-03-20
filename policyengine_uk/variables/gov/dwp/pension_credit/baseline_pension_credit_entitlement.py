from policyengine_uk.model_api import *


class baseline_pension_credit_entitlement(Variable):
    label = "PC entitlement (baseline)"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
