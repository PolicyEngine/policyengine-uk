from policyengine_uk.model_api import *


class is_resolved_household_head(Variable):
    value_type = bool
    entity = Person
    label = "Household head, exactly one per household"
    documentation = (
        "The household head every programme uses: the household reference "
        "person, a householder in whose name the accommodation is owned or "
        "rented. Exactly one member of each household is the head. It is "
        "the member is_household_head flags; where that input flags more "
        "than one member, the eldest flagged member; where it flags none, "
        "the eldest member. A tie in age goes to the member listed first "
        "among the people. "
        "Read this, or benunit_contains_household_head, rather than "
        "is_household_head, so that rent, non-dependant and Council Tax "
        "Reduction rules agree on whose household it is."
    )
    definition_period = YEAR

    def formula(person, period, parameters):
        household = person.household
        age = person("age", period)
        flagged = person("is_household_head", period)
        # get_rank sorts stably, so a tie in age goes to the member listed
        # first and exactly one member has rank 0.
        rank = where(
            household.any(flagged),
            person.get_rank(household, -age, condition=flagged),
            person.get_rank(household, -age),
        )
        return rank == 0
