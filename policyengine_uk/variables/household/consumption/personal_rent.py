from policyengine_uk.model_api import *


class personal_rent(Variable):
    value_type = float
    entity = Person
    label = "Rent liable"
    documentation = "The gross rent this person is liable for"
    definition_period = YEAR
    unit = GBP
    defined_for = "is_household_head"
    adds = ["rent"]
