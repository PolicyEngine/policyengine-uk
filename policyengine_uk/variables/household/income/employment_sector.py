from policyengine_uk.model_api import *


class EmploymentSector(Enum):
    NOT_EMPLOYED = "Not in paid employment"
    PRIVATE = "Private sector"
    PUBLIC = "Public sector"


class employment_sector(Variable):
    value_type = Enum
    entity = Person
    possible_values = EmploymentSector
    default_value = EmploymentSector.NOT_EMPLOYED
    label = "Employer sector (public or private) of the person's main job"
    documentation = (
        "Whether the person's main job is in the public or private sector. "
        "Sourced from the FRS `mjobsect` field; NOT_EMPLOYED where the person "
        "has no main job."
    )
    definition_period = YEAR
