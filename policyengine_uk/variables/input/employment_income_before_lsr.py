from policyengine_uk.model_api import *


class employment_income_before_lsr(Variable):
    value_type = float
    entity = Person
    label = "employment income before labor supply responses"
    unit = GBP
    definition_period = YEAR
    uprating = "gov.obr.per_capita.employment_income"
