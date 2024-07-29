from policyengine_uk.model_api import *


class interest_income(Variable):
    label = "interest income"
    documentation = "Income from interest on savings."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW
