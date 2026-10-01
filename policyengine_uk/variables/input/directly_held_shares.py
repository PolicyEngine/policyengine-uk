from policyengine_uk.model_api import *


class directly_held_shares(Variable):
    label = "directly held shares"
    documentation = (
        "Value of shares the household holds directly, outside ISAs and pooled "
        "funds: shares in UK companies, listed or not, and employee shares and "
        "share options. Part of corporate_wealth, so the two must never be "
        "summed. The Enhanced FRS imputes it from the Wealth and Assets Survey "
        "(UK shares plus employee shares and options); overseas shares are not "
        "yet imputed. Quoted shares are valued for the means tests at their "
        "price less 10% for the expenses of sale (Advice for Decision Making "
        "H1665)."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"
    quantity_type = STOCK
    default_value = 0
