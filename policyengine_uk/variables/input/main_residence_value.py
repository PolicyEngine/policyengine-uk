from policyengine_uk.model_api import *


class main_residence_value(Variable):
    label = "main residence value"
    documentation = (
        "Total value of the main residence. Set tenure_type to an owner tenure "
        "for owner-only charges such as the High Value Council Tax Surcharge. "
        "Excluded from Universal Credit capital under Schedule 10 paragraph 1."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"
