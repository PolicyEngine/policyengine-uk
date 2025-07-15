from policyengine_uk.model_api import *


class is_married(Variable):
    value_type = bool
    entity = BenUnit
    label = "Married"
    documentation = "Whether the benefit unit adults are married to each other or in a civil partnership"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return add(benunit, period, ["is_adult"]) == 2
