from policyengine_uk.model_api import *


class other_property_value(Variable):
    label = "Other property value"
    documentation = (
        "Gross value of other real estate with unspecified geography and "
        "property type. Included in worldwide property wealth and the regional "
        "property-to-land approximation, but not UK property purchase values."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK
    default_value = 0
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"
