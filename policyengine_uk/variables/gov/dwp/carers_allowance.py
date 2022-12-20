from policyengine_uk.model_api import *


class carers_allowance(Variable):
    value_type = float
    entity = Person
    label = "Carer's Allowance"
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        receives_ca = person("carers_allowance_reported", period) > 0
        rate = parameters(period).gov.dwp.carers_allowance.rate
        return receives_ca * rate * WEEKS_IN_YEAR


class carers_allowance_reported(Variable):
    value_type = float
    entity = Person
    label = "Carer's Allowance (reported)"
    definition_period = YEAR
    unit = GBP
