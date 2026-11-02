from policyengine_uk.model_api import *


class non_savings_income_after_allowances(Variable):
    value_type = float
    entity = Person
    label = "Non-savings, non-dividend income for Income Tax after allowances"
    documentation = (
        "The model subtracts savings income, dividend income and allowances "
        "from net income and floors the result at zero, so it sets allowances "
        "against this income first. Parliament treats savings and dividends "
        "as the highest part of income, above this income (ITA 2007 s. 16). "
        "It raises the rate limits by the grossed-up Gift Aid gift "
        "(s. 414(2)(b)), which does not reduce this taxable income. "
        "property_income_tax, taxable_property_income_after_allowances, the "
        "Marriage Allowance rate test and, for Scottish taxpayers, tax_band "
        "read it."
    )
    definition_period = YEAR
    reference = dict(
        title="Income Tax Act 2007, s. 16",
        href="https://www.legislation.gov.uk/ukpga/2007/3/section/16",
    )
    unit = GBP

    def formula(person, period, parameters):
        return max_(
            0,
            # Not adjusted_net_income: it deducts the grossed-up Gift Aid
            # gift (ITA 2007 s. 58), which raises the rate limits instead
            # (s. 414(2)(b)) and is no deduction from taxable income.
            person("net_income", period)
            - person("taxable_savings_interest_income", period)
            - person("taxable_dividend_income", period)
            - person("allowances", period),
        )
