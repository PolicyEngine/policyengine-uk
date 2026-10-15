from policyengine_uk.model_api import *


class allowances(Variable):
    value_type = float
    entity = Person
    label = "Allowances applicable to adjusted net income"
    definition_period = YEAR
    unit = GBP

    # ITA 2007 s.414(2): Gift Aid extends rate limits rather than deducting
    # the gift from the income charged to tax.
    adds = [
        "personal_allowance",
        "blind_persons_allowance",
        "covenanted_payments",
        "charitable_investment_gifts",
        "other_deductions",
        "pension_contributions_relief",
    ]
