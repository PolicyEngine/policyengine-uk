from policyengine_uk.model_api import *


class beer_litres(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    label = "Annual litres of beer"
    unit = "litre"
    uprating = "gov.economic_assumptions.indices.obr.per_capita.alcohol_clearances.beer_and_cider"
