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


class receives_carer_support_payment(Variable):
    value_type = bool
    entity = Person
    label = "receives Carer Support Payment"
    documentation = "Whether this person receives Carer Support Payment."
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("carer_support_payment", period) > 0


class receives_carer_benefit(Variable):
    value_type = bool
    entity = Person
    label = "receives a carer benefit"
    documentation = (
        "Whether this person receives Carer's Allowance or the Scottish "
        "Carer Support Payment."
    )
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("receives_carers_allowance", period) | person(
            "receives_carer_support_payment", period
        )
