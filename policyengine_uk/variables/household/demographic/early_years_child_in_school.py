from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.highest_education import (
    EducationType,
)

# Primary education or a later stage. A 4- or 5-year-old in full-time
# education can be recorded at a later stage than primary, so all of them
# count.
SCHOOL_STAGES = (
    EducationType.PRIMARY,
    EducationType.LOWER_SECONDARY,
    EducationType.UPPER_SECONDARY,
    EducationType.POST_SECONDARY,
    EducationType.TERTIARY,
)


class early_years_child_in_school(Variable):
    value_type = bool
    entity = Person
    label = "early years child in school"
    documentation = (
        "Whether a child of early years age has started school: "
        "current_education is primary or a later stage. In England that is "
        "a reception class, whose place meets the universal and working "
        "parent entitlements, so no funded hours are given outside it. In "
        "Scotland it is primary 1, after which a child is no longer an "
        "eligible pre-school child for funded early learning and childcare. "
        "Without a current_education input a 4-year-old is not in school, "
        "since the age default for 4- to 6-year-olds is "
        "NOT_COMPLETED_PRIMARY. Primary includes fee-paying independent "
        "schools, whose reception children can still take funded hours: set "
        "this to false for them."
    )
    definition_period = YEAR
    reference = (
        "https://www.gov.uk/government/publications/early-education-and-childcare--2/early-education-and-childcare-valid-from-1-april-2026",
        "https://www.legislation.gov.uk/asp/2014/8/section/47",
    )

    def formula(person, period, parameters):
        education = person("current_education", period)
        return np.logical_or.reduce([education == stage for stage in SCHOOL_STAGES])
