from policyengine_uk.model_api import *


class wealth_tax(Variable):
    label = "Wealth tax"
    documentation = (
        "Annual tax on household net wealth: the wealth tax schedule applied to "
        "net_wealth, which is total_wealth (property, corporate and private "
        "pension wealth and savings) less mortgage, consumer and student loan "
        "debt. Net wealth at or below zero bears no tax."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        wealth = household("net_wealth", period)
        tax = parameters(period).gov.contrib.ubi_center.wealth_tax
        return tax.calc(wealth)
