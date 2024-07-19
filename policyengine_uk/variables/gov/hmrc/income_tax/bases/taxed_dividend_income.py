from policyengine_uk.model_api import *


class taxed_dividend_income(Variable):
    value_type = float
    entity = Person
    label = "Dividend income which is taxed"
    definition_period = YEAR
    unit = GBP
    reference = dict(
        title="Income Tax (Trading and Other Income) Act 2005 s. 383",
        href="https://www.legislation.gov.uk/ukpga/2005/5/section/383",
    )

    def formula(person, period, parameters):
        return max_(
            0,
            person("taxable_dividend_income", period)
            - person("received_allowances_dividend_income", period)
            - person("dividend_allowance", period),
        )
