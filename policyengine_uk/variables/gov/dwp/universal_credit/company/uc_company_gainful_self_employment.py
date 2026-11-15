from policyengine_uk.model_api import *


class uc_company_gainful_self_employment(Variable):
    value_type = bool
    entity = Person
    label = "Universal Credit treats the person as gainfully self-employed through an owned company"
    documentation = (
        "Whether Universal Credit treats the person as in gainful "
        "self-employment because they stand as sole owner or partner of a "
        "company carrying on a trade and their activities in the course of "
        "that trade are their main employment. The minimum income floor then "
        "applies (unless they are in a start-up period)."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="The Universal Credit Regulations 2013 reg. 77(3)(c)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/77",
        ),
        dict(
            title="The Universal Credit Regulations (Northern Ireland) 2016 regs. 77(3)(c) and 63",
            href="https://www.legislation.gov.uk/nisr/2016/216/regulation/77",
        ),
        dict(
            title="Advice for Decision Making, Chapter H4, para. H4375",
            href="https://www.gov.uk/government/publications/advice-for-decision-making-staff-guide",
        ),
    ]

    def formula(person, period, parameters):
        return (
            person("uc_company_owner_treatment_applies", period)
            & person("owned_company_carries_on_trade", period)
            & person("owned_company_is_main_employment", period)
        )
