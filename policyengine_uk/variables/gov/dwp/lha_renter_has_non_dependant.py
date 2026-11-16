from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.LHA_allowed_bedrooms import (
    other_family_non_dependants,
)


class lha_renter_has_non_dependant(Variable):
    value_type = bool
    entity = BenUnit
    label = "LHA renter has a non-dependant (Universal Credit)"
    documentation = (
        "Universal Credit: someone in this benefit unit who is a Universal "
        "Credit non-dependant (is_benefit_unit_non_dependant_for_universal_credit: "
        "aged 16 or over and neither the claimant or partner, a qualifying "
        "young person nor the renter's foster child), or, for the claim "
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
        "renter's extended benefit unit is responsible for (para 9(2)(g)). "
        "The test uses Universal Credit's own qualifying young person (reg "
        "5), not Housing Benefit's or a rule for every 16-year-old: a Child "
        "Benefit young person past the Universal Credit terminal date is a "
        "non-dependant here. Housing Benefit uses "
        "housing_benefit_has_non_dependant."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/9",
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/28",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/2",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/5",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        # UC Regs 2013 Sch 4 para 9(1)(c) and (2)(a)-(d), (g): a member of the
        # renter's benefit unit aged 16 or over who is neither the claimant or
        # partner, a qualifying young person (reg 5) nor the renter's foster
        # child (para 9(2)(c), (3)). There is no separate rule for
        # 16-year-olds: one outside reg 5 is a non-dependant (para 28(4)), and
        # one within it is a qualifying young person the renter is
        # responsible for (para 28(3)) unless no one in the extended benefit
        # unit is (para 9(2)(g)), so outside that case the renter is not a
        # specified renter either way.
        within_benefit_unit = benunit.any(
            person("is_benefit_unit_non_dependant_for_universal_credit", period)
        )
        # UC Regs 2013 Sch 4 para 28(4): "no person is a non-dependant in
        # relation to the renter". The people from other families whom the
        # counting claim treats as its non-dependants are those whose
        # bedrooms LHA_allowed_bedrooms counts in that claim (para 9(1)(c)
        # and 9(2)), so the flag reads the same helper.
        counted = benunit("uc_non_dependants_counted", period)
        non_dependant = other_family_non_dependants(benunit, period)
        other_family = counted * benunit.max(person.household.sum(non_dependant))
        return within_benefit_unit | (other_family > 0)
