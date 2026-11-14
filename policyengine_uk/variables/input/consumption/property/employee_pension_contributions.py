from policyengine_uk.model_api import *


class employee_pension_contributions(Variable):
    label = "employee pension contributions"
    documentation = (
        "Actual reported employee pension contributions, plus any explicitly "
        "supplied legacy return to ordinary pay/member payments. The "
        "NIC-only salary-sacrifice excess is not a member contribution."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    adds = [
        "employee_pension_contributions_reported",
        "salary_sacrifice_returned_to_income",
    ]
