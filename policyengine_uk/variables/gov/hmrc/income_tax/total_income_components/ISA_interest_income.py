from policyengine_uk.model_api import *


class individual_savings_account_interest_income(Variable):
    value_type = float
    entity = Person
    label = "Amount received in interest from Individual Savings Accounts"
    definition_period = YEAR
    unit = GBP
    reference = dict(
        title="Income Tax (Trading and Other Income) Act 2005, Part VI, s. 3",
        href="https://www.legislation.gov.uk/ukpga/2005/5/part/6/chapter/3",
    )
