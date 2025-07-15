from policyengine_uk.model_api import *


class baseline_income_support_entitlement(Variable):
    label = "Income Support eligible (baseline)"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
