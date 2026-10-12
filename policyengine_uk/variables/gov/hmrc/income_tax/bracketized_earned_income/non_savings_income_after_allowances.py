from policyengine_uk.model_api import *


class non_savings_income_after_allowances(Variable):
    value_type = float
    entity = Person
    label = "Non-savings, non-dividend income for Income Tax after allowances"
    documentation = (
        "Adjusted net income less savings and dividend income and allowances, "
        "floored at nil: the income below savings and dividends (ITA 2007 s. "
        "16) once the allowances, which go to it first, are taken off. "
        "property_income_tax and taxable_property_income_after_allowances "
        "both read it."
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
            person("adjusted_net_income", period)
            - person("taxable_savings_interest_income", period)
            - person("taxable_dividend_income", period)
            - person("allowances", period),
        )
