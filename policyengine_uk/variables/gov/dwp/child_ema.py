from policyengine_uk.model_api import *


class child_ema(Variable):
    label = "Child EMA"
    documentation = "Educational Maintenance Allowance for children"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
