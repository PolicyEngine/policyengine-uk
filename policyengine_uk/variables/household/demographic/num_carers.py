from policyengine_uk.model_api import *


class num_carers(Variable):
    value_type = int
    entity = BenUnit
    label = "Number of carers in the family"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return add(benunit, period, ["is_carer_for_benefits"])
