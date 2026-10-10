from policyengine_uk.model_api import *
from policyengine_uk.utils.income_tax import calc_income_tax_with_gift_aid


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
        gross_gift = person("gift_aid_grossed_up", period)
        tax_with_dividends = calc_income_tax_with_gift_aid(
            rates.dividends, other_income + dividends_after_allowances, gross_gift
        )
        tax_with_dividend_allowance = calc_income_tax_with_gift_aid(
            rates.dividends, other_income + dividend_allowance, gross_gift
        )
        return max_(0, tax_with_dividends - tax_with_dividend_allowance)
