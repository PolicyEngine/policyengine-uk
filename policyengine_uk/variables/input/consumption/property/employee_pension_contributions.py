from policyengine_uk.model_api import *


class employee_pension_contributions(Variable):
    label = "employee pension contributions"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    uprating = "gov.obr.per_capita.employment_income"
