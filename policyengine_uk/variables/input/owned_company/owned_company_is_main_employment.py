from policyengine_uk.model_api import *


class owned_company_is_main_employment(Variable):
    value_type = bool
    entity = Person
    label = "owned company trade is main employment"
    documentation = (
        "Whether the person's activities in the course of the trade of the "
        "company in which they stand as sole owner or partner are their main "
        "employment."
    )
    definition_period = YEAR
    default_value = False
    reference = dict(
        title="The Universal Credit Regulations 2013 reg. 77(3)(c)",
        href="https://www.legislation.gov.uk/uksi/2013/376/regulation/77",
    )
