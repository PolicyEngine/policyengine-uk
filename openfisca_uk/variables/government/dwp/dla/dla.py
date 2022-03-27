from openfisca_uk.model_api import *


class dla(Variable):
    label = "Disability Living Allowance"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    formula = sum_of_variables(["dla_sc", "dla_m"])
