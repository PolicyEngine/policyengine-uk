from policyengine_uk.model_api import *


class received_personal_allowance(Variable):

    value_type = float
    entity = Person
    label = (
        "Total Personal Allowance received by an individual in a given year"
    )
    unit = GBP
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 35"

    adds = [
        "received_personal_allowance_earned_income",
        "received_personal_allowance_savings",
        "received_personal_allowance_dividends",
    ]
