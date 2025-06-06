from policyengine_uk.model_api import *


class maternity_allowance_reported(Variable):
    value_type = float
    entity = Person
    label = "Maternity allowance"
    definition_period = YEAR
    unit = GBP
