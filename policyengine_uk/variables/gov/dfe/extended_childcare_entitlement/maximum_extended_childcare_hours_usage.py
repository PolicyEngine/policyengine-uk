from policyengine_uk.model_api import *


class maximum_extended_childcare_hours_usage(Variable):
    value_type = float
    entity = BenUnit
    label = "maximum extended childcare hours used"
    documentation = "The maximum number of weekly extended childcare hours that this family uses"
    definition_period = YEAR
    default_value = 30  # By default, uses up to 30 hours per week
