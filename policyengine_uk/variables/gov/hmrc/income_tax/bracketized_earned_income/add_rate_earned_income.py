from policyengine_uk.model_api import *


class add_rate_earned_income(Variable):
    value_type = float
    entity = Person
    label = "Earned income (non-savings, non-dividend) at the additional rate"
    definition_period = YEAR
    unit = GBP
    reference = dict(
        title="Income Tax Act 2007, s. 10",
        href="https://www.legislation.gov.uk/ukpga/2007/3/section/10",
    )

    def formula(person, period, parameters):
        income = person("earned_taxable_income", period)
        thresholds = parameters(period).gov.hmrc.income_tax.rates.uk.thresholds
        return clip(income, thresholds[2], inf) - thresholds[2]
