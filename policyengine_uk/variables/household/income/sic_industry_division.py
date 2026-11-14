from policyengine_uk.model_api import *


class sic_industry_division(Variable):
    value_type = int
    entity = Person
    label = "Standard Industrial Classification (2007) division of the main or last job"
    documentation = (
        "Two-digit SIC 2007 division of the person's main job, or of their "
        "last job if they are not in work (0 if unknown). Sourced from the FRS "
        "`sic` field; the FRS asks the employment questions of everyone who "
        "has ever worked, so use employment_status to select current jobs. "
        "Division 84 = 'Public administration and defence; compulsory social "
        "security'."
    )
    default_value = 0
    definition_period = YEAR
