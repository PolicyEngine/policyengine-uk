from policyengine_uk.model_api import *

label = "Care"


class receives_carers_allowance(Variable):
    value_type = bool
    entity = Person
    label = "receives Carer's Allowance"
    documentation = "Whether this person receives Carer's Allowance."
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("carers_allowance", period) > 0
