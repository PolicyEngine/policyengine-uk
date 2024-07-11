from policyengine_uk.model_api import *


class uc_mif_applies(Variable):
    value_type = bool
    entity = Person
    label = "Universal Credit minimum income floor applies"
    documentation = "Whether the Minimum Income Floor should be used to determine UC entitlement"
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/62/2021-04-06"
    )
    definition_period = YEAR

    def formula(person, period, parameters):
        has_self_empl_income = person("self_employment_income", period) > 0
        in_startup_period = person("uc_is_in_startup_period", period)
        return has_self_empl_income & ~in_startup_period
