from policyengine_uk.model_api import *


class maternity_allowance(Variable):
    label = "Maternity Allowance"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    adds = ["maternity_allowance_reported"]
