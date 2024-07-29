from policyengine_uk.model_api import *


class pension_credit_entitlement(Variable):
    label = "PC entitlement"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    defined_for = "is_pension_credit_eligible"
    adds = ["guarantee_credit", "savings_credit"]
