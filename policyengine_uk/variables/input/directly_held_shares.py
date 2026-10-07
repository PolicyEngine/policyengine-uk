from policyengine_uk.model_api import *


class directly_held_shares(Variable):
    label = "directly held shares"
    documentation = (
        "Value of shares the household holds directly, outside ISAs and pooled "
        "funds: shares in UK companies, listed or not (the Wealth and Assets "
        "Survey question), and employee shares and share options. Part of "
        "corporate_wealth, so the two must never be summed. Imputed for the "
        "Enhanced FRS from the Wealth and Assets Survey's UK shares and "
        "employee shares and options (policyengine-uk-data#501); overseas "
        "shares are not imputed. Quoted shares are valued at their price less "
        "10% for the expenses of sale (Advice for Decision Making H1665 for "
        "Universal Credit; Decision Makers' Guide 29671, 52671 and 84763 for "
        "Income Support and JSA, ESA and Pension Credit); unquoted shares need "
        "an expert valuation (ADM H1679-H1681)."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"
    quantity_type = STOCK
    default_value = 0
