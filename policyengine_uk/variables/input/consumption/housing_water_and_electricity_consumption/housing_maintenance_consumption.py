from policyengine_uk.model_api import *


class housing_maintenance_consumption(Variable):
    label = "housing maintenance spending"
    documentation = "Total spending on maintenance of the home."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW

