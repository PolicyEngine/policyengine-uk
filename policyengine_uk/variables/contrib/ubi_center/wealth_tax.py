from policyengine_uk.model_api import *


class wealth_tax(Variable):
    label = "Wealth tax"
    documentation = "Annual tax on household net wealth"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        wealth = household("total_wealth", period)
        tax = parameters(period).gov.contrib.ubi_center.wealth_tax
        return tax.calc(wealth)
