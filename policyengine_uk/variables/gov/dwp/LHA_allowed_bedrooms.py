from policyengine_uk.model_api import *
import pandas as pd
import warnings
from policyengine_core.model_api import *

warnings.filterwarnings("ignore")


def bedrooms_for_children(benunit, period):
    """Bedrooms for the family's children under 16.

    Children must share rooms in pairs unless they are opposite-sex and one
    is 10 or over. This is the minimum number of bedrooms that allocates them
    under those rules.
    """
    person = benunit.members
    age = person("age", period)
    male = person("is_male", period)
    under_16 = age < 16
    under_10 = age < 10
    child_over_10 = ~under_10 & under_16
    boys_under_10 = benunit.sum(under_10 & male)
    boys_over_10 = benunit.sum(child_over_10 & male)
    girls_under_10 = benunit.sum(under_10 & ~male)
    girls_over_10 = benunit.sum(child_over_10 & ~male)
    # First, have over-10s share where possible
    over_10_rooms = (boys_over_10 + 1) // 2 + (girls_over_10 + 1) // 2
    # There may children over 10 still not sharing
    space_for_boy_under_10 = boys_over_10 % 2
    space_for_girl_under_10 = girls_over_10 % 2
    # Have those spaces filled where possible by children under 10
    left_over_boys_under_10 = max_(boys_under_10 - space_for_boy_under_10, 0)
    left_over_girls_under_10 = max_(girls_under_10 - space_for_girl_under_10, 0)
    # The remaining children must share in pairs
    under_10_rooms = (left_over_boys_under_10 + left_over_girls_under_10 + 1) // 2
    return over_10_rooms + under_10_rooms


class LHA_allowed_bedrooms(Variable):
    value_type = float
    entity = BenUnit
    label = "The number of bedrooms covered by LHA for the benefit unit"
    documentation = (
        "Universal Credit size criteria: one bedroom for the renter or "
        "couple, one for each non-dependant aged 16 or over, and the "
        "children's bedrooms. Joint tenants and other sharers of the rent, "
        "boarders and lodgers are not non-dependants, so they add no bedroom "
        "to anyone's entitlement; only the household head's family has "
        "non-dependants (see is_non_dependant_of_household_head)."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/9",
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/10",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        aged_16_or_over = person("age", period) >= 16
        # UC Regs 2013 Sch 4 para 10(1)(c): a non-dependant who is not a child.
        non_dependant = aged_16_or_over & person(
            "is_non_dependant_of_household_head", period
        )
        head_family = benunit.any(person("is_household_head", period))
        non_dependants = head_family * benunit.max(person.household.sum(non_dependant))
        return 1 + non_dependants + bedrooms_for_children(benunit, period)
