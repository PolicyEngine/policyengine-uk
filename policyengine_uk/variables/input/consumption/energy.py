from policyengine_uk.model_api import *

label = "Energy"
description = "Energy consumption."


class domestic_energy_consumption(Variable):
    label = "Domestic energy consumption"
    documentation = "Combined gas and electric bills."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.consumer_price_index"
