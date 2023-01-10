from policyengine_uk.model_api import *


class incapacity_benefit(Variable):
    value_type = float
    entity = Person
    label = "Incapacity Benefit"
    definition_period = YEAR
    unit = GBP

    adds = ["incapacity_benefit_reported"]


class incapacity_benefit_reported(Variable):
    value_type = float
    entity = Person
    label = "Incapacity Benefit (reported)"
    definition_period = YEAR
    unit = GBP
