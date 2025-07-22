from policyengine_uk.model_api import *


class incapacity_benefit(Variable):
    label = "Incapacity Benefit"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    adds = ["incapacity_benefit_reported"]
