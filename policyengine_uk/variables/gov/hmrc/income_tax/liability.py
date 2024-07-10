from policyengine_uk.model_api import *





class taxed_dividend_income(Variable):
    value_type = float
    entity = Person
    label = "Dividend income which is taxed"
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        return max_(
            0,
            person("taxable_dividend_income", period)
            - person("dividend_allowance", period),
        )



