from policyengine_uk.model_api import *


class baseline_child_benefit_entitlement(Variable):
    label = "Child Benefit (baseline)"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
