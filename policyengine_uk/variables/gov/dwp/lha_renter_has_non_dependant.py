from policyengine_uk.model_api import *


def has_non_dependant_in_benefit_unit(benunit, period):
    """Whether someone in the benefit unit is neither a claimant or partner
    nor a child or young person, nor a child or young person placed with the
    family as a foster child or for adoption."""
    person = benunit.members
    claimant_or_partner = person("is_claimant_or_partner", period)
    # A child or young person under either scheme (UC reg 5; HB reg 19)
    # is a dependant, not a non-dependant.
    age = person("age", period)
    # A foster child or a child placed for adoption is not a non-dependant
    # either (UC Sch 4 para 9(2)(c) and (g); HB reg 3(2)(c) and reg 21(3)).
    child_or_qyp = (
        person("is_child_or_qualifying_young_person_for_universal_credit", period)
        | person("is_child_or_young_person_for_legacy_benefits", period)
        | person("is_child_or_young_person_placed_with_family", period)
        | ((age >= 16) & (age < 17))
    )
    return benunit.any(~claimant_or_partner & ~child_or_qyp)


class lha_renter_has_non_dependant(Variable):
    value_type = bool
    entity = BenUnit
    label = "LHA renter has a non-dependant (Universal Credit)"
    documentation = (
        "Universal Credit: someone in this benefit unit who is neither a "
        "claimant or partner nor a child or young person, or, for the "
        "household head's family, a claimant or partner of another family "
        "who is a non-dependant of the household head (see "
        "is_non_dependant_of_household_head): joint tenants and other "
        "sharers of the rent, boarders and lodgers are not non-dependants, "
        "and a non-dependant counts in one Universal Credit claim only, which "
        "the model gives to the household head's family. A child or young "
        "person placed with the family as a foster child or for adoption is "
        "not a non-dependant. Housing Benefit has its own test: see "
        "housing_benefit_claimant_has_non_dependant."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/9",
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/28",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        within_benefit_unit = has_non_dependant_in_benefit_unit(benunit, period)
        # UC Regs 2013 Sch 4 para 9(2)(d)-(f).
        non_dependant_claimants = person("is_claimant_or_partner", period) & person(
            "is_non_dependant_of_household_head", period
        )
        head_family = benunit.any(person("is_household_head", period))
        other_family_non_dependants = head_family * benunit.max(
            person.household.sum(non_dependant_claimants)
        )
        return within_benefit_unit | (other_family_non_dependants > 0)
