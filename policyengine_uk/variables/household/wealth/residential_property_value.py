from policyengine_uk.model_api import *


class residential_property_value(Variable):
    label = "Residential property value"
    documentation = (
        "Gross value of domestic residential property: the main residence "
        "plus other residential property, which combines second homes and "
        "buy-to-let holdings. Overseas and unclassified other real estate "
        "cannot be classified as residential from their aggregate values."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK

    adds = ["main_residence_value", "other_residential_property_value"]
