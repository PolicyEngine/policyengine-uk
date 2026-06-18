from policyengine_uk.model_api import *


class sic_industry_division(Variable):
    value_type = int
    entity = Person
    label = "Standard Industrial Classification (2007) division of the main job"
    documentation = (
        "Two-digit SIC 2007 division of the person's main job (0 if unknown). "
        "Sourced from the FRS `sic` field. Division 84 = 'Public administration "
        "and defence; compulsory social security'."
    )
    default_value = 0
    definition_period = YEAR
