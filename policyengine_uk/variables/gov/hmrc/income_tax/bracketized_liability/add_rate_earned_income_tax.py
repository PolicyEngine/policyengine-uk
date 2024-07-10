from policyengine_uk.model_api import *


class add_rate_earned_income_tax(Variable):
    value_type = float
    entity = Person
    label = "Income tax on earned income at the additional rate"
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        amount = person("add_rate_earned_income", period)
        return (
            parameters(period).gov.hmrc.income_tax.rates.uk.rates[2] * amount
        )