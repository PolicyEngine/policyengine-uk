from policyengine_uk.model_api import *


class water_and_sewerage_charges(Variable):
    value_type = float
    entity = Household
    label = "water and sewerage charges"
    documentation = "Total amount spent on water and sewerage charges"
    definition_period = YEAR
    # No `uprating` attribute: the dataset projection uprates this by country
    # (uprate_water_charges in policyengine_uk/data/economic_assumptions.py),
    # as it does council tax, because Scotland and Northern Ireland do not
    # follow the Ofwat path for England and Wales.
