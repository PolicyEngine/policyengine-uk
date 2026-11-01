from policyengine_uk.model_api import *


class is_apprentice(Variable):
    value_type = bool
    entity = Person
    label = "In an apprenticeship programme"
    documentation = (
        "Whether this person is an apprentice. Employer National Insurance "
        "relief uses this status at any apprenticeship year. For the apprentice "
        "minimum wage at age 19 or over, also supply "
        "is_in_first_year_of_apprenticeship."
    )
    definition_period = YEAR
    default_value = False
