from policyengine_uk.model_api import *


class taxable_dividend_income(Variable):
    value_type = float
    entity = Person
    label = "Amount of dividend income that is taxable"
    definition_period = YEAR
    reference = dict(
        title="Income Tax Act (Trading and Other Income) 2005, s. 383",
        href="https://www.legislation.gov.uk/ukpga/2005/5/section/383",
    )
    unit = GBP

    def formula(person, period, parameters):
        return max_(
            0,
            person("dividend_income", period)
            - person("deficiency_relief", period),
        )
