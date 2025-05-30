from policyengine_uk.model_api import *


class is_carer_for_benefits(Variable):
    value_type = bool
    entity = Person
    label = "Whether this person is a carer for benefits purposes"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("receives_carers_allowance", period)
