from policyengine_uk.model_api import *


class taxed_savings_income(Variable):
    value_type = float
    entity = Person
    label = "Savings income which advances the person's income tax schedule"
    definition_period = YEAR
    reference = dict(
        title="Income Tax Act 2007, s. 11D",
        href="https://www.legislation.gov.uk/ukpga/2007/3/section/11D",
    )
    unit = GBP

    adds = [
        "basic_rate_savings_income",
        "higher_rate_savings_income",
        "add_rate_savings_income",
    ]
