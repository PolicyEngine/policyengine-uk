from policyengine_uk.model_api import *


class uc_company_owner_treatment_applies(Variable):
    value_type = bool
    entity = Person
    label = "Universal Credit treats the person as a company's sole owner or partner"
    documentation = (
        "Whether the person stands in a position analogous to a sole owner or "
        "partner in relation to a company that carries on a trade or a "
        "property business, so that Universal Credit treats them as that sole "
        "owner or partner. This does not apply where the person derives "
        "employed earnings from the company under the intermediaries or "
        "managed service company rules from their main employment."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="The Universal Credit Regulations 2013 reg. 77(1) and (5)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/77",
        ),
        dict(
            title="The Universal Credit Regulations (Northern Ireland) 2016 reg. 77(1) and (5)",
            href="https://www.legislation.gov.uk/nisr/2016/216/regulation/77",
        ),
    ]

    def formula(person, period, parameters):
        carries_on_business = person("owned_company_carries_on_trade", period) | person(
            "owned_company_carries_on_property_business", period
        )
        return (
            person("stands_as_sole_owner_or_partner_of_company", period)
            & carries_on_business
            & ~person("owned_company_income_is_intermediary_employed_earnings", period)
        )
