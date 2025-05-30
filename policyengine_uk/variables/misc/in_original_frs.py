from policyengine_uk.model_api import *


class in_original_frs(Variable):
    label = "In original FRS"
    entity = Household
    documentation = "Whether this household appeared in the original FRS, or whether it has been modified."
    definition_period = YEAR
    value_type = float
    unit = GBP
