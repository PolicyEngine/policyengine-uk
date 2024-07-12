from policyengine_uk.model_api import *


class savings_income_tax(Variable):
    value_type = float
    entity = Person
    label = "Income tax on savings income"
    definition_period = YEAR
    reference = dict(
        title="Income Tax Act 2007, s. 11D",
        href="https://www.legislation.gov.uk/ukpga/2007/3/section/11D",
    )
    unit = GBP

    def formula(person, period, parameters):
        rates = parameters(period).gov.hmrc.income_tax.rates.uk.rates
        basic_rate_amount = person("basic_rate_savings_income", period)
        higher_rate_amount = person("higher_rate_savings_income", period)
        add_rate_amount = person("add_rate_savings_income", period)
        return (
            rates[0] * basic_rate_amount
            + rates[1] * higher_rate_amount
            + rates[2] * add_rate_amount
        )
