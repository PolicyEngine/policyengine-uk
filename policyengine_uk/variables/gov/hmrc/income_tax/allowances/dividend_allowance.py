from policyengine_uk.model_api import *


class dividend_allowance(Variable):
    value_type = float
    entity = Person
    label = "Dividend allowance for the person"
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 13A"
    unit = GBP

    def formula(person, period, parameters):
        # Take maximum allowance
        max_allowance = parameters(period).gov.hmrc.income_tax.allowances.dividend_allowance

        # Find remaining coverable dividend income
        remaining_dividend_income = person("taxable_dividend_income", period) - person("personal_allowance_dividend_income", period)

        # Find eligible amount
        calculated_amount = min_(max_allowance, remaining_dividend_income)

        # Ensure negatives return 0
        return max_(
            0,
            calculated_amount
        )
