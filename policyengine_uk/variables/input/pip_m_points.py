from policyengine_uk.model_api import *


class pip_m_points(Variable):
    label = "PIP mobility points"
    documentation = "Total descriptor points scored across the two Schedule 1 Part 3 mobility activities. Used to derive `pip_m_category` when the category is not provided as input."
    entity = Person
    definition_period = YEAR
    value_type = int
    default_value = 0
