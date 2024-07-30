from policyengine_uk.model_api import *


class defined_contribution_pensions(Variable):
    label = "defined-contribution pension wealth"
    documentation = "Value of all defined-contribution pensions."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK

