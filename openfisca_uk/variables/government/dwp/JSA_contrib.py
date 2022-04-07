from openfisca_uk.model_api import *


@uprated(by="september_cpi")
class JSA_contrib(Variable):
    value_type = float
    entity = Person
    label = "JSA (contribution-based)"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(person, period, parameters):
        return person("JSA_contrib_reported", period)


class JSA_contrib_reported(Variable):
    value_type = float
    entity = Person
    label = "Job Seeker's Allowance (contribution-based) (reported)"
    definition_period = YEAR
    unit = "currency-GBP"
