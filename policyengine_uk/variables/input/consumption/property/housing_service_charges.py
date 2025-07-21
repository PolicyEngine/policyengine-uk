from policyengine_uk.model_api import *


class housing_service_charges(Variable):
    value_type = float
    entity = Household
    label = "housing service charges"
    documentation = "Total amount spent on housing service charges"
    definition_period = YEAR
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.lagged_average_earnings"
