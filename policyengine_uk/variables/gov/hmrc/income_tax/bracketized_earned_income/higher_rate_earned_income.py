from policyengine_uk.model_api import *


class higher_rate_earned_income(Variable):
    value_type = float
    entity = Person
    label = "Earned income (non-savings, non-dividend) at the higher rate"
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        income = person("earned_taxable_income", period)
        thresholds = parameters(period).gov.hmrc.income_tax.rates.uk.thresholds
        return clip(income, thresholds[1], thresholds[2]) - thresholds[1]