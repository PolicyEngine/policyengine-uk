from policyengine_uk.model_api import *


class social_security_income(Variable):
    value_type = float
    entity = Person
    label = "Income from social security for tax purposes"
    definition_period = YEAR
    reference = "Income Tax (Earnings and Pensions) Act 2003 s. 1(1)(b)"
    unit = GBP

    adds = [
        "state_pension",
        "incapacity_benefit",
        "jsa_contrib_reported",
        "esa_contrib_reported",
        "carers_allowance",
    ]
