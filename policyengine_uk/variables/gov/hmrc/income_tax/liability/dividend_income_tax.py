from policyengine_uk.model_api import *


class dividend_income_tax(Variable):
    value_type = float
    entity = Person
    label = "Income tax on dividend income"
    definition_period = YEAR
    reference = dict(
        title="Income Tax Act 2007, s. 13",
        href="https://www.legislation.gov.uk/ukpga/2007/3/section/13",
    )
    unit = GBP

    def formula(person, period, parameters):
        rates = parameters(period).gov.hmrc.income_tax.rates
        other_income = person("earned_taxable_income", period) + person(
            "taxed_savings_income", period
        )
        taxable_dividends = person("taxed_dividend_income", period)
        tax_with_dividends = rates.dividends.calc(
            other_income + taxable_dividends
        )
        tax_without_dividends = rates.dividends.calc(other_income)
        return max_(0, tax_with_dividends - tax_without_dividends)
