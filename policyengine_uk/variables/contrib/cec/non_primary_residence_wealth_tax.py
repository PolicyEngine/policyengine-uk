from policyengine_uk.model_api import *


class non_primary_residence_wealth_tax(Variable):
    label = "Wealth tax (non-primary residence)"
    documentation = (
        "Annual tax on gross household wealth excluding the primary residence. "
        "The tax base deducts no mortgage or other debt."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        wealth = household("total_wealth", period)
        primary_residence = household("main_residence_value", period)
        tax = parameters(period).gov.contrib.cec.non_primary_residence_wealth_tax
        return tax.calc(max_(0, wealth - primary_residence))
