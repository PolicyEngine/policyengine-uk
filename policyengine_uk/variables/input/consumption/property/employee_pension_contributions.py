from policyengine_uk.model_api import *


class employee_pension_contributions(Variable):
    label = "employee pension contributions"
    documentation = "Total employee pension contributions including adjustments for salary sacrifice cap reforms"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.average_earnings"
    adds = [
        "employee_pension_contributions_reported",
        "salary_sacrifice_returned_to_income",
    ]
