from policyengine_uk.model_api import *


class owned_company_capital(Variable):
    value_type = float
    entity = Person
    label = "owned company capital"
    documentation = (
        "The value of the capital of the company in which the person stands "
        "as sole owner or partner, or the person's share of that value. DWP "
        "guidance takes the company's net value (its capital less its "
        "liabilities) and a person's share as their fraction of its shares. "
        "Includes any assets used wholly and exclusively for the company's "
        "trade (recorded again in owned_company_trade_assets)."
    )
    definition_period = YEAR
    unit = GBP
    default_value = 0
    quantity_type = STOCK
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"
    reference = [
        dict(
            title="The Universal Credit Regulations 2013 reg. 77(2)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/77",
        ),
        dict(
            title="Advice for Decision Making, Chapter H1, paras. H1892-H1893",
            href="https://www.gov.uk/government/publications/advice-for-decision-making-staff-guide",
        ),
    ]
