from policyengine_uk.model_api import *


class car_first_registration_date(Variable):
    value_type = date
    entity = Person
    definition_period = YEAR
    label = "First registration date of the car kept by this person"
    unit = "date"
    default_value = date(9999, 1, 1)
