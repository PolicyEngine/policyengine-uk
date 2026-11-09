from policyengine_uk.model_api import *


class main_residential_property_purchased_is_in_uk(Variable):
    value_type = bool
    entity = Household
    label = "Main home bought is in the UK"
    documentation = "Whether the main residential property bought this year is land in the United Kingdom. The household's current address does not establish the purchased property's location."
    definition_period = YEAR
    quantity_type = STOCK
    default_value = False
    reference = "https://www.legislation.gov.uk/uksi/1998/1870/schedule/paragraph/6"
