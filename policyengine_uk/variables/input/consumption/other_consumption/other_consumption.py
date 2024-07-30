from policyengine_uk.model_api import *


class other_consumption(Variable):
    label = "other consumption"
    documentation = "Covers categories 12 in pre-2018 COICOP and 12 and 13 in COICOP 2018. Includes insurance, financial services, personal care, social protection and miscellaneous goods."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW

