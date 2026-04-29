from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.highest_education import (
    EducationType,
)


class bursary_fund_16_to_19_in_qualifying_education(Variable):
    value_type = bool
    entity = Person
    label = "In qualifying education for 16 to 19 Bursary Fund"
    documentation = (
        "Whether the student is in a qualifying publicly funded post-16 study programme. "
        "This can be set explicitly in simulations; by default it uses post-secondary education "
        "and excludes apprenticeships."
    )
    definition_period = YEAR
    set_input = set_input_dispatch_by_period

    def formula(person, period, parameters):
        return (
            person("current_education", period) == EducationType.POST_SECONDARY
        ) & ~person("is_apprentice", period)
