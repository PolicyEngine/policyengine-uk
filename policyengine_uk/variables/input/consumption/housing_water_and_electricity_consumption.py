from policyengine_uk.model_api import *

# The below variables follow the COICOP MECE categories.


class housing_water_and_electricity_consumption(Variable):
    entity = Household
    label = "housing, water and electricity consumption"
    documentation = (
        "Total yearly expenditure on housing, water and electricity"
    )
    unit = GBP
    definition_period = YEAR
    value_type = float
    quantity_type = FLOW
    uprating = "gov.economic_assumptions.indices.obr.consumer_price_index"
