from policyengine_uk.model_api import *


class iidb(Variable):
    value_type = float
    entity = Person
    label = "Industrial Injuries Disablement Benefit"
    definition_period = YEAR
    unit = GBP

    adds = ["iidb_reported"]
