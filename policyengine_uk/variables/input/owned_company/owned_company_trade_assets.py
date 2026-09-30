from policyengine_uk.model_api import *


class owned_company_trade_assets(Variable):
    value_type = float
    entity = Person
    label = "owned company trade assets"
    documentation = (
        "The part of owned_company_capital made up of the company's assets "
        "that are used wholly and exclusively for the purposes of its trade."
    )
    definition_period = YEAR
    unit = GBP
    default_value = 0
    quantity_type = STOCK
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"
    reference = dict(
        title="The Universal Credit Regulations 2013 reg. 77(3)(a)",
        href="https://www.legislation.gov.uk/uksi/2013/376/regulation/77",
    )
