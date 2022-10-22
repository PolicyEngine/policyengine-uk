from policyengine_uk.model_api import *


class armed_forces_independence_payment(Variable):
    label = "Armed Forces Independence Payment"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
