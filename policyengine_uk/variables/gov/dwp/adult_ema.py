from policyengine_uk.model_api import *


class adult_ema(Variable):
    label = "Adult EMA"
    documentation = "Educational Maintenance Allowance for adults"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
