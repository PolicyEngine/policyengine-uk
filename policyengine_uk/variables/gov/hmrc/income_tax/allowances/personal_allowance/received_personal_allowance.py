from policyengine_uk.model_api import *


class received_personal_allowance(Variable):

    value_type = float
    entity = Person
    label = "Total Personal Allowance received by an individual in a given year"
    unit = GBP
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 35"

    adds = [
        "personal_allowance_earned_taxable_income",
        "personal_allowance_savings_income",
        "personal_allowance_dividend_income",
    ]