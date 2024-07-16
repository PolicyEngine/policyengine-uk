from policyengine_uk.model_api import *


class personal_allowance(Variable):
    # The order in which segments of the Personal Allowance
    # are calculated is found in Income Tax Act 2007, chapter 2, section 16 (5)

    value_type = float
    entity = Person
    label = "Personal Allowance for the year"
    unit = GBP
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 35"

    adds = [
        "personal_allowance_earned_taxable_income",
        "personal_allowance_savings_income",
        "personal_allowance_dividend_income",
    ]
