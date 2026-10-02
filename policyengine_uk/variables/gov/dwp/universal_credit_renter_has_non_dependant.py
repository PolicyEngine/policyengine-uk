from policyengine_uk.model_api import *


class universal_credit_renter_has_non_dependant(Variable):
    value_type = bool
    entity = BenUnit
    label = "Universal Credit renter has a non-dependant"
    documentation = (
        "Whether any person is a non-dependant in relation to the renter, the "
        "third condition for a specified renter. A member of the renter's "
        "benefit unit is one if aged 16 or over and neither the claimant or "
        "partner nor a qualifying young person (see "
        "is_benefit_unit_non_dependant_for_universal_credit), other than a "
        "foster child of the renter (see is_lha_foster_child). For the "
        "household head's family, so is a member of another family of the "
        "household who is not liable for rent (see "
        "is_non_dependant_of_household_head). A non-dependant counts in one "
        "claim only, so a sharer of the rent, boarder or lodger outside the "
        "head's family has only their own benefit unit's. Housing Benefit has its "
        "own test: see housing_benefit_claimant_has_non_dependant."
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
        # UC Regs 2013 Sch 4 para 9(1)(c) and (2)(a), (g): a member of the
        # renter's benefit unit outside the claimant, partner and qualifying
        # young persons. The qualifying young person test is the model's
        # (reg 5), with no separate rule for 16-year-olds: one outside it is
        # a non-dependant, one within it is a qualifying young person the
        # renter is responsible for, and either fails para 28.
        # Para 9(2)(c): the renter's foster child is not a non-dependant. The
        # model reads "foster child" (para 9(3)) as a looked-after person
        # under 18 placed with the renter, following the foster parent
        # definition in reg 2; the Welfare Reform Act 2012 s.40 definition of
        # a child (under 16) would instead make a looked-after 16- or
        # 17-year-old who is not a qualifying young person a non-dependant.
        within_benefit_unit = benunit.any(
            person("is_benefit_unit_non_dependant_for_universal_credit", period)
            & ~person("is_lha_foster_child", period)
        )
        # Para 9(2)(d)-(f): members of another family who is not liable for
        # rent, counted in the household head's claim only. The same people
        # as uc_non_dep_deductions charges, so a contribution always implies
        # a non-dependant.
        other_family = person("is_non_dependant_of_household_head", period)
        head_family = benunit.any(person("is_household_head", period))
        from_other_families = head_family & (
            benunit.max(person.household.sum(other_family)) > 0
        )
        return within_benefit_unit | from_other_families
