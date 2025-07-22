from policyengine_uk.model_api import *


class healthy_start_vouchers(Variable):
    label = "healthy start vouchers"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
