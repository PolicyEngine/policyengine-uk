from policyengine_uk.model_api import *


class savings_starter_rate_income(Variable):
    value_type = float
    entity = Person
    label = "Savings income which is tax-free under the starter rate"
    definition_period = YEAR
    reference = dict(
        title="Income Tax Act 2007, s. 12",
        href="https://www.legislation.gov.uk/ukpga/2007/3/section/12",
    )
    unit = GBP

    def formula(person, period, parameters):
        income = person("basic_rate_savings_income_pre_starter", period)
        limit = parameters(
            period
        ).gov.hmrc.income_tax.rates.savings_starter_rate.allowance
        return max_(0, limit - income)
