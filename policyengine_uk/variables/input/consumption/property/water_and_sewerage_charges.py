from policyengine_uk.model_api import *


class water_and_sewerage_charges(Variable):
    value_type = float
    entity = Household
    label = "water and sewerage charges"
    documentation = "Total amount spent on water and sewerage charges"
    definition_period = YEAR
    uprating = "gov.economic_assumptions.indices.ofwat.water_bills"
