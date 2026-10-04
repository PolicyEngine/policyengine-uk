from policyengine_uk.model_api import *


class uc_mif_applies(Variable):
    value_type = bool
    entity = Person
    label = "Universal Credit minimum income floor applies"
    documentation = (
        "Whether the minimum income floor applies to this person: a claimant "
        "with a self-employment profit or loss, outside a start-up period."
    )
    reference = "https://www.legislation.gov.uk/uksi/2013/376/regulation/62"
    definition_period = YEAR

    def formula(person, period, parameters):
        # Reg. 62(1) applies to a claimant, not a dependant, in gainful
        # self-employment: a trade carried on in expectation of profit (reg.
        # 64), so a trading loss counts (ADM H4503).
        claimant = person("is_uc_claimant", period)
        has_self_empl_income = person("self_employment_income", period) != 0
        in_startup_period = person("uc_is_in_startup_period", period)
        return claimant & has_self_empl_income & ~in_startup_period
