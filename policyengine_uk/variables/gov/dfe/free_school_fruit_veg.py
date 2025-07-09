from policyengine_uk.model_api import *


class free_school_fruit_veg(Variable):
    label = "free school fruit and vegetables"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
