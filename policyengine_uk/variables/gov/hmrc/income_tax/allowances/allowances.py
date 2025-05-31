from policyengine_uk.model_api import *


class allowances(Variable):
    value_type = float
    entity = Person
    label = "Allowances applicable to adjusted net income"
    definition_period = YEAR
    unit = GBP

    adds = [
        "personal_allowance",
        "blind_persons_allowance",
        "gift_aid",
        "covenanted_payments",
        "charitable_investment_gifts",
        "other_deductions",
        "pension_contributions_relief",
    ]
