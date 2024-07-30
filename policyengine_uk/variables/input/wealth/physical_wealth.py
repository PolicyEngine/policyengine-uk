from policyengine_uk.model_api import *


class physical_wealth(Variable):
    label = "physical wealth"
    documentation = "Estimated value of all physical possessions."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK
