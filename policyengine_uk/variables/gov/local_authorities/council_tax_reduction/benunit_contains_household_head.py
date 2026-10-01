from policyengine_uk.model_api import *


class benunit_contains_household_head(Variable):
    value_type = bool
    entity = BenUnit
    label = "Benefit unit contains the household head"
    documentation = (
        "Whether the household head is in this family. The head is the "
        "household reference person: a householder, in whose name the "
        "accommodation is owned or rented, and so the resident liable for the "
        "council tax under the Local Government Finance Act 1992 (s.6 in "
        "England and Wales, s.75 in Scotland), which the Council Tax Reduction "
        "classes of applicant require. Each household has exactly one head. "
        "Where the input flags more than one member, the eldest flagged member "
        "is the head; where it flags none, the eldest member is."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/1992/14/section/6",
        "https://www.legislation.gov.uk/ukpga/1992/14/section/75",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        household = person.household
        age = person("age", period)
        flagged = person("is_household_head", period)
        # get_rank breaks ties in age by order within the household, so
        # exactly one member has rank 0.
        rank = where(
            household.any(flagged),
            person.get_rank(household, -age, condition=flagged),
            person.get_rank(household, -age),
        )
        return benunit.any(rank == 0)
