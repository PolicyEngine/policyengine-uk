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
        "couple, one for each member of the benefit unit aged 16 or over who "
        "is not the claimant or partner, one for each non-dependant aged 16 or "
        "over, and the children's bedrooms. A qualifying young person the "
        "renter is responsible for has their own bedroom; any other member "
        "aged 16 or over is a non-dependant and has one too. A qualifying "
        "young person no one is responsible for, such as one looked after by "
        "a local authority, is not a non-dependant and has no bedroom, in "
        "this family or another. Joint tenants and other sharers "
        "of the rent, boarders and lodgers are not non-dependants, so they "
        "add no bedroom to anyone's entitlement; only the household head's "
        "family has non-dependants from other families (see "
        "is_non_dependant_of_household_head)."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/9",
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/10",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/4",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/5",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        # A child is a person under 16 (WRA 2012 s.40).
        aged_16_or_over = person("age", period) >= 16
        family_member = aged_16_or_over & ~person("is_claimant_or_partner", period)
        qualifying = person("is_qualifying_young_person_for_universal_credit", period)
        responsible = person(
            "is_child_or_qualifying_young_person_for_universal_credit", period
        )
        # UC Regs 2013 Sch 4 para 9(2)(g): a qualifying young person for whom
        # no one is responsible (reg 4(6), such as one looked after by a local
        # authority) is not a non-dependant, in this family or another.
        no_one_responsible = qualifying & ~responsible
        # Para 10(1)(b): a qualifying young person for whom the renter is
        # responsible (regs 4 and 5).
        qualifying_young_person = family_member & responsible
        # Para 10(1)(c) with para 9(2): any other member aged 16 or over is a
        # non-dependant.
        family_non_dependant = family_member & ~qualifying
        family_rooms = benunit.sum(qualifying_young_person | family_non_dependant)
        # Para 10(1)(c): a non-dependant from another family who is not a
        # child.
        non_dependant = (
            aged_16_or_over
            & ~no_one_responsible
            & person("is_non_dependant_of_household_head", period)
        )
        head_family = benunit.any(person("is_household_head", period))
        non_dependants = head_family * benunit.max(person.household.sum(non_dependant))
        return (
            1 + family_rooms + non_dependants + bedrooms_for_children(benunit, period)
        )
