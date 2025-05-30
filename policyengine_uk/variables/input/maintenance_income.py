from policyengine_uk.model_api import *


class maintenance_income(Variable):
    value_type = float
    entity = Person
    label = "maintenance payment income"
    documentation = "Income from maintenance payments to you"
    definition_period = YEAR
    unit = GBP
    uprating = "gov.obr.per_capita.non_labour_income"
