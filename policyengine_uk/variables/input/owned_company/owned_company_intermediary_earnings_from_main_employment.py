from policyengine_uk.model_api import *


class owned_company_intermediary_earnings_from_main_employment(Variable):
    value_type = bool
    entity = Person
    label = "owned company intermediary earnings derive from main employment"
    documentation = (
        "Whether the income recorded in "
        "owned_company_intermediary_earnings_chapter derives from activities "
        "that are the person's main employment."
    )
    definition_period = YEAR
    default_value = False
    reference = dict(
        title="The Universal Credit Regulations 2013 reg. 77(5)",
        href="https://www.legislation.gov.uk/uksi/2013/376/regulation/77",
    )
