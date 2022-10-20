from policyengine_uk.model_api import *


class pip(Variable):
    label = "Personal Independence Payment"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    formula = sum_of_variables(["pip_dl", "pip_m"])


class PIPCategory(Enum):
    STANDARD = "Standard"
    ENHANCED = "Enhanced"
    NONE = "None"
