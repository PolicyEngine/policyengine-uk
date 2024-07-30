from policyengine_uk.model_api import *


class defined_benefit_pensions(Variable):
    label = "defined-benefit pension wealth"
    documentation = "Value of all defined-benefit pensions."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK

