from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.LHA_allowed_bedrooms import (
    other_family_non_dependants,
)


class lha_renter_has_non_dependant(Variable):
    value_type = bool
    entity = BenUnit
    label = "LHA renter has a non-dependant (Universal Credit)"
    documentation = (
        "Universal Credit: someone in this benefit unit who is neither a "
        "claimant or partner nor a child or young person, or, for the claim "
        "that counts the household's non-dependants (see "
        "uc_non_dependants_counted), anyone that claim treats as a "
        "non-dependant from another family (see other_family_non_dependants). "
        "These are the people whose bedrooms the claim's size criteria count: "
        "the Universal Credit non-dependants of other families "
        "(is_uc_non_dependant_of_household_head), such as the adult son, who "
        "pays nothing, of a lodger whose family makes no claim of its own; "
        "the non-dependants within a family that neither claims nor counts "
        "the household's non-dependants; and a foster child aged 16 or 17 "
        "who is not a qualifying young person, in a family that does not "
        "count the household's non-dependants. A renter with any of them "
        "fails the third condition in UC Regs 2013 Sch 4 para 28(4), so para "
        "27's shared accommodation rate does not apply to them. Joint "
        "tenants and other "
        "sharers of the rent, boarders and lodgers are not non-dependants, and "
        "the flag leaves out a child or qualifying young person no one in the "
        "renter's extended benefit unit is responsible for (para 9(2)(g)). A "
        "child or young person placed with the family as a foster child or "
        "for adoption is not the renter's non-dependant. Housing Benefit uses "
        "housing_benefit_has_non_dependant."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/9",
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/28",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/3",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/21",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        claimant_or_partner = person("is_claimant_or_partner", period)
        # A child or young person under either scheme (UC reg 5; HB reg 19)
        # is a dependant, not a non-dependant.
        age = person("age", period)
        # A foster child or a child placed for adoption is not a
        # non-dependant either (UC Sch 4 para 9(2)(c) and (g); HB reg 3(2)(c)
        # and reg 21(3)).
        child_or_qyp = (
            person("is_child_or_qualifying_young_person_for_universal_credit", period)
            | person("is_child_or_young_person_for_legacy_benefits", period)
            | person("is_child_or_young_person_placed_with_family", period)
            | ((age >= 16) & (age < 17))
        )
        within_benefit_unit = benunit.any(~claimant_or_partner & ~child_or_qyp)
        # UC Regs 2013 Sch 4 para 28(4): "no person is a non-dependant in
        # relation to the renter". The people from other families whom the
        # counting claim treats as its non-dependants are those whose
        # bedrooms LHA_allowed_bedrooms counts in that claim (para 9(1)(c)
        # and 9(2)), so the flag reads the same helper.
        counted = benunit("uc_non_dependants_counted", period)
        non_dependant = other_family_non_dependants(benunit, period)
        other_family = counted * benunit.max(person.household.sum(non_dependant))
        return within_benefit_unit | (other_family > 0)
