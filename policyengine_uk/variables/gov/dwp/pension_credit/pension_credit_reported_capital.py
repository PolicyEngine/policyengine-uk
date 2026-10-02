from policyengine_uk.model_api import *


class pension_credit_reported_capital(Variable):
    value_type = float
    entity = BenUnit
    label = "reported Pension Credit capital"
    documentation = (
        "Capital of the claimant and partner as recorded for this benefit unit, "
        "such as a survey's benefit-unit capital measure. When it is 0 or more "
        "it replaces the household-level proxy in Pension Credit assessable "
        "capital: Pension Credit counts the claimant's capital and, under the "
        "State Pension Credit Act 2002 s. 5, the partner's, and no one else's. "
        "The default, -1, means none is "
        "recorded and the household proxy applies. Set it to 0 to record no "
        "capital."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = STOCK
    default_value = -1
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"
    reference = "https://www.legislation.gov.uk/ukpga/2002/16/section/5"
