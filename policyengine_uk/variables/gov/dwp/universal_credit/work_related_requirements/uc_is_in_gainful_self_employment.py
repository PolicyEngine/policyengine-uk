from policyengine_uk.model_api import *


class uc_is_in_gainful_self_employment(Variable):
    value_type = bool
    entity = Person
    label = "In gainful self-employment for Universal Credit"
    documentation = (
        "Whether the person is in gainful self-employment: carrying on a "
        "trade, profession or vocation as their main employment, with "
        "self-employed earnings from it, that is organised, developed, "
        "regular and carried on in expectation of profit. The Secretary of "
        "State determines it. Without an input, the model reads any "
        "self-employment profit or loss as gainful self-employment, and no "
        "profit or loss as none; set this for a trader who breaks even, or "
        "for self-employment that is not gainful."
    )
    reference = "https://www.legislation.gov.uk/uksi/2013/376/regulation/64"
    definition_period = YEAR

    def formula(person, period, parameters):
        # A trade carried on in expectation of profit (reg. 64(c)), so a
        # trading loss counts (ADM H4503).
        return person("self_employment_income", period) != 0
