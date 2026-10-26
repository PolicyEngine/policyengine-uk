from policyengine_uk.model_api import *


class overseas_property_value(Variable):
    label = "Overseas property value"
    documentation = (
        "Gross value of overseas land and property, including time-shares. "
        "Included in worldwide property wealth and excluded from UK land "
        "estimates and UK property purchase values."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK
    default_value = 0
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"
