from policyengine_uk.model_api import *


class care_hours(Variable):
    label = "hours providing care"
    documentation = "Weekly hours providing care to others"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = "hour"
