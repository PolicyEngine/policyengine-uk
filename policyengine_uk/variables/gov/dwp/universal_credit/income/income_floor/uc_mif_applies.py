from policyengine_uk.model_api import *


class uc_mif_applies(Variable):
    value_type = bool
    entity = Person
    label = "Universal Credit minimum income floor applies"
    documentation = (
        "Whether the Minimum Income Floor should be used to determine UC entitlement"
    )
    reference = [
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/62/2021-04-06",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/77",
        "https://www.legislation.gov.uk/nisr/2016/216/regulation/63",
    ]
    definition_period = YEAR

    def formula(person, period, parameters):
        has_self_empl_income = person("self_employment_income", period) > 0
        # A person whose main employment is the trade of a company they stand
        # as sole owner or partner of is treated as gainfully self-employed,
        # so the floor applies (UC Regs 2013 reg. 77(3)(c)). Not modelled for
        # either route: reg. 62(1)(b) limits the floor to claimants subject to
        # all work-related requirements.
        company_gainful_self_employment = person(
            "uc_company_gainful_self_employment", period
        )
        in_startup_period = person("uc_is_in_startup_period", period)
        return (
            has_self_empl_income | company_gainful_self_employment
        ) & ~in_startup_period
