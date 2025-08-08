from policyengine_uk.model_api import *


class council_tax(Variable):
    value_type = float
    entity = Household
    label = "Council Tax"
    documentation: str = "Gross amount spent on Council Tax, before discounts"
    definition_period = YEAR
    unit = GBP
    quantity_type = FLOW
