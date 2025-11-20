from policyengine_uk.model_api import *


class employment_income(Variable):
    value_type = float
    entity = Person
    label = "employment income"
    documentation = "Total income from employment. Include wages, bonuses, tips, etc. This should be gross of all private pension contributions."
    definition_period = YEAR
    unit = GBP
    reference = "Income Tax (Earnings and Pensions) Act 2003 s. 1(1)(a)"
    quantity_type = FLOW
    adds = [
        "employment_income_before_lsr",
        "employment_income_behavioral_response",
        "employer_ni_fixed_employer_cost_change",
    ]
    uprating = "gov.economic_assumptions.indices.obr.average_earnings"
