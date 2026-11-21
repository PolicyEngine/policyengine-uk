from policyengine_uk.model_api import *


class firm_employees(Variable):
    value_type = int
    entity = Firm
    label = "Number of employees"
    documentation = "Number of employees on the firm's payroll in the year (headcount)."
    definition_period = YEAR
    unit = "person"
