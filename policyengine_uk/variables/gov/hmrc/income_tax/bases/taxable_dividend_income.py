from policyengine_uk.model_api import *


class taxable_dividend_income(Variable):
    value_type = float
    entity = Person
    label = "Amount of dividend income that is taxable"
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 383"
    unit = GBP

    def formula(person, period, parameters):
        return max_(
            0,
            person("dividend_income", period)
            - person("deficiency_relief", period)
        )
