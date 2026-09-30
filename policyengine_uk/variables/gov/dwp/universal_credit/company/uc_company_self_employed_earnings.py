from policyengine_uk.model_api import *


class uc_company_self_employed_earnings(Variable):
    value_type = float
    entity = Person
    label = "Universal Credit self-employed earnings from an owned company"
    documentation = (
        "The income of a company carrying on a trade, or the person's share "
        "of it, which Universal Credit treats as the person's self-employed "
        "earnings when they stand as the company's sole owner or partner. It "
        "is in addition to any pay they receive as the company's director or "
        "employee. A company that carries on only a property business gives "
        "no earnings. Where the minimum income floor applies it is compared "
        "with the person's total earned income, including this amount and "
        "their pay (reg. 62(2)); DWP guidance (ADM H4375) describes comparing "
        "the company income alone."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="The Universal Credit Regulations 2013 reg. 77(3)(b) and (4)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/77",
        ),
        dict(
            title="Advice for Decision Making, Chapter H4, paras. H4374 and H4376",
            href="https://www.gov.uk/government/publications/advice-for-decision-making-staff-guide",
        ),
    ]

    def formula(person, period, parameters):
        trading_company_owner = person(
            "uc_company_owner_treatment_applies", period
        ) & person("owned_company_carries_on_trade", period)
        return where(
            trading_company_owner,
            person("owned_company_income_share", period),
            0,
        )
