from policyengine_uk.model_api import *


class iidb(Variable):
    value_type = float
    entity = Person
    label = "Industrial Injuries Disablement Benefit"
    definition_period = YEAR
    unit = GBP

    adds = ["iidb_reported"]


class iidb_reported(Variable):
    value_type = float
    entity = Person
    label = "Industrial Injuries Disablement Benefit (reported)"
    definition_period = YEAR
    unit = GBP
    uprating = "gov.benefit_uprating_cpi"
