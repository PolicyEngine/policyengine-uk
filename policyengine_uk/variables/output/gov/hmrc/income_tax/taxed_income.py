from policyengine_uk.model_api import *


class taxed_income(Variable):
    value_type = float
    entity = Person
    label = "Income which is taxed"
    definition_period = YEAR
    unit = GBP
    reference = dict(
        title="Income Tax Act 2007 s. 23",
        href="https://www.legislation.gov.uk/ukpga/2007/3/section/23",
    )

    adds = [
        "earned_taxable_income",
        "taxed_savings_income",
        "taxed_dividend_income",
    ]
