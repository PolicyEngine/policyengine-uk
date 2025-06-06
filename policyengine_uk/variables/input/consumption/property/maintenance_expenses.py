from policyengine_uk.model_api import *


class maintenance_expenses(Variable):
    value_type = float
    entity = Person
    label = "maintenance expenses"
    definition_period = YEAR
    unit = GBP
