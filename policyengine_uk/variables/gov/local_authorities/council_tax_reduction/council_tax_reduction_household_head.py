from policyengine_uk.model_api import *


class council_tax_reduction_household_head(Variable):
    value_type = bool
    entity = Person
    label = "Household head for Council Tax Reduction"
    documentation = (
        "The member Council Tax Reduction treats as the household head: the "
        "household reference person, exactly one per household. Where the "
        "input flags more than one member, the eldest flagged member is the "
        "head; where it flags none, the eldest member is. Ties go by order."
    )
    definition_period = YEAR

    def formula(person, period, parameters):
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
        return rank == 0
