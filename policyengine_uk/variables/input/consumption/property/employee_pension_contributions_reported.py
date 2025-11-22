from policyengine_uk.model_api import *


class employee_pension_contributions_reported(Variable):
    label = "employee pension contributions (reported)"
    documentation = "Employee pension contributions as reported in survey data, before any adjustments for salary sacrifice reforms"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.average_earnings"
