from policyengine_uk.model_api import *


class uc_company_capital(Variable):
    value_type = float
    entity = Person
    label = "Universal Credit capital treated as held from an owned company"
    documentation = (
        "The value of the company's capital, or the person's share of it, "
        "which Universal Credit treats the person as possessing when they "
        "stand as the company's sole owner or partner. Assets used wholly and "
        "exclusively for the company's trade are disregarded while the person "
        "is engaged in activities in the course of that trade. This follows "
        "the regulation: DWP guidance (ADM H4372) instead disregards all of "
        "the company capital while the person works in the business, and "
        "H1880 paraphrases the test as 'wholly or mainly', both closer to the "
        "older Income Support rule."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = STOCK
    reference = [
        dict(
            title="The Universal Credit Regulations 2013 reg. 77(2) and (3)(a)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/77",
        ),
        dict(
            title="Advice for Decision Making, Chapter H4, paras. H4367 and H4371-H4373",
            href="https://www.gov.uk/government/publications/advice-for-decision-making-staff-guide",
        ),
    ]

    def formula(person, period, parameters):
        applies = person("uc_company_owner_treatment_applies", period)
        trade_assets_disregarded = person(
            "owned_company_carries_on_trade", period
        ) & person("is_engaged_in_owned_company_trade", period)
        disregarded = where(
            trade_assets_disregarded,
            person("owned_company_trade_assets", period),
            0,
        )
        capital = max_(0, person("owned_company_capital", period) - disregarded)
        return where(applies, capital, 0)
