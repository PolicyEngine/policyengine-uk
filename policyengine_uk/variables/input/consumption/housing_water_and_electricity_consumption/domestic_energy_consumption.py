from policyengine_uk.model_api import *


class domestic_energy_consumption(Variable):
    label = "domestic energy consumption"
    documentation = "Combined gas and electricity spending within the home."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW
