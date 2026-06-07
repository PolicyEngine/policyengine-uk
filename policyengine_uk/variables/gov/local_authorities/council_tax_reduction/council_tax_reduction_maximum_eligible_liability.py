from policyengine_uk.model_api import *


class council_tax_reduction_maximum_eligible_liability(Variable):
    value_type = float
    entity = Household
    label = "Maximum Council Tax liability eligible for CTR"
    definition_period = YEAR
    unit = GBP

    def formula(household, period, parameters):
        return household("council_tax", period)
