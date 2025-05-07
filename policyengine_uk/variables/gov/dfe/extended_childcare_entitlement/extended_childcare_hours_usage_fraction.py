from policyengine_uk.model_api import *


class extended_childcare_hours_usage_fraction(Variable):
    value_type = float
    entity = BenUnit
    label = "fraction of maximum extended childcare hours used"
    documentation = "The fraction (0-1) of the maximum available extended childcare hours that this family uses"
    definition_period = YEAR
    default_value = 1.0  # By default, uses 100% of available hours
