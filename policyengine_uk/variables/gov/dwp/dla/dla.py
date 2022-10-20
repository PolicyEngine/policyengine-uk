from policyengine_uk.model_api import *


class dla(Variable):
    label = "Disability Living Allowance"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    formula = sum_of_variables(["dla_sc", "dla_m"])
