from policyengine_uk.model_api import *


class water_charges(Variable):
    label = "water charges"
    documentation = "Charges for water and sewerage."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW
