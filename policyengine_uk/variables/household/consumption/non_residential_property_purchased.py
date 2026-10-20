from policyengine_uk.model_api import *


class non_residential_property_purchased(Variable):
    label = "Non-residential property bought"
    documentation = (
        "The price paid for the purchase of a non-residential property in the "
        "year. Only include the value of a single purchase. A main-residence "
        "purchase (property_purchased) does not imply one: the household's "
        "stock of non-residential property (non_residential_property_value) is "
        "not a purchase, so this is nil unless set directly or by a dataset "
        "that imputes non-residential purchases."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
