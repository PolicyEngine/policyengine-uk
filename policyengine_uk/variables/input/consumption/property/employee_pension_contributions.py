from policyengine_uk.model_api import *


class employee_pension_contributions(Variable):
    label = "employee pension contributions"
    documentation = (
        "Total employee pension contributions including reported contributions "
        "and any excess salary sacrifice redirected to regular pension contributions."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    adds = [
        "employee_pension_contributions_reported",
        "salary_sacrifice_returned_to_income",
    ]
