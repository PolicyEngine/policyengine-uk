from policyengine_uk.model_api import *


class owned_company_holding_value(Variable):
    value_type = float
    entity = Person
    label = "value of holding in owned company"
    documentation = (
        "The value of the person's holding (their shares) in the company in "
        "which they stand as sole owner or partner, to the extent that it is "
        "already counted in the household's capital (for example within "
        "corporate_wealth) or in uc_reported_capital."
    )
    definition_period = YEAR
    unit = GBP
    default_value = 0
    quantity_type = STOCK
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"
    reference = dict(
        title="The Universal Credit Regulations 2013 reg. 77(2)",
        href="https://www.legislation.gov.uk/uksi/2013/376/regulation/77",
    )
