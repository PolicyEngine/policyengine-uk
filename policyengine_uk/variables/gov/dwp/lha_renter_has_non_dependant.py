from policyengine_uk.model_api import *


class lha_renter_has_non_dependant(Variable):
    value_type = bool
    entity = BenUnit
    label = "LHA renter has a non-dependant (Universal Credit)"
    documentation = (
        "Universal Credit: someone in this benefit unit who is neither a "
        "claimant or partner nor a child or young person, or, for the claim "
        "that counts the household's non-dependants (see "
        "uc_non_dependants_counted), anyone in another family who is a "
        "Universal Credit non-dependant of the renter "
        "(is_uc_non_dependant_of_household_head), such as a lodger's adult "
        "son who pays nothing. Joint tenants and other sharers of the rent, "
        "boarders and lodgers are not non-dependants, and the flag leaves "
        "out a boarder's or lodger's child or qualifying young person (UC "
        "Regs 2013 Sch 4 para 9(2)(g)). The model does not identify foster "
        "children. Housing Benefit uses housing_benefit_has_non_dependant."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/9",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/3",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        claimant_or_partner = person("is_claimant_or_partner", period)
        # A child or young person under either scheme (UC reg 5; HB reg 19)
        # is a dependant, not a non-dependant.
        age = person("age", period)
        child_or_qyp = (
            person("is_child_or_qualifying_young_person_for_universal_credit", period)
            | person("is_child_or_young_person_for_legacy_benefits", period)
            | ((age >= 16) & (age < 17))
        )
        within_benefit_unit = benunit.any(~claimant_or_partner & ~child_or_qyp)
        # UC Regs 2013 Sch 4 para 9(1)(c) and 9(2): the non-dependants of
        # other families, whoever in the family they are. A boarder's or
        # lodger's non-paying adult son counts; their child or qualifying
        # young person does not (para 9(2)(g)).
        other_family_non_dependant = person(
            "is_uc_non_dependant_of_household_head", period
        )
        counted = benunit("uc_non_dependants_counted", period)
        other_family_non_dependants = counted * benunit.max(
            person.household.sum(other_family_non_dependant)
        )
        return within_benefit_unit | (other_family_non_dependants > 0)
