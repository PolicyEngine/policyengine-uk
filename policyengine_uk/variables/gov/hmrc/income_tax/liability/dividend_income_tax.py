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
        other_income = person("earned_taxable_income", period) + max_(
            0,
            person("taxable_savings_interest_income", period)
            - person("received_allowances_savings_income", period),
        )
        dividends_after_allowances = max_(
            0,
            person("taxable_dividend_income", period)
            - person("received_allowances_dividend_income", period),
        )
        dividend_allowance = min_(
            parameters(period).gov.hmrc.income_tax.allowances.dividend_allowance,
            dividends_after_allowances,
        )
        tax_with_dividends = rates.dividends.calc(
            other_income + dividends_after_allowances
        )
        tax_with_dividend_allowance = rates.dividends.calc(
            other_income + dividend_allowance
        )
        return max_(0, tax_with_dividends - tax_with_dividend_allowance)
