from policyengine_uk.model_api import *


class uc_non_dep_deductions(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit non-dependent deductions"
    documentation = (
        "Housing cost contributions for the renter's non-dependants: those in "
        "other families of the household, for the household head's family "
        "only, and those within the renter's own benefit unit. None if the "
        "renter or a joint renter is exempt."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/9",
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/13",
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/15",
    )

    def formula(benunit, period, parameters):
        # A housing cost contribution is deducted for each non-dependant in
        # the renter's extended benefit unit (UC Regs 2013 Sch 4 para 13).
        person = benunit.members
        deductions = person("uc_individual_non_dep_deduction", period)
        # Non-dependants from other families live outside the household
        # head's family and are not liable for rent. A non-dependant counts
        # in one claim only (para 9(2)(f)), which the model gives to the
        # household head's family, so a sharer, boarder or lodger has none
        # from other families.
        other_family = person("is_non_dependant_of_household_head", period)
        head_family = benunit.any(person("is_household_head", period))
        from_other_families = head_family * benunit.max(
            person.household.sum(deductions * other_family)
        )
        # A member of the renter's own benefit unit who is not the claimant,
        # partner or a qualifying young person is a non-dependant of the
        # renter (para 9(1)(c) and (2)(a), (g)).
        own_family = (
            person("is_benefit_unit_non_dependant_for_universal_credit", period)
            & ~other_family
        )
        from_own_family = benunit.sum(deductions * own_family)
        renter_exempt = benunit("uc_non_dep_deductions_renter_exempt", period)
        return where(renter_exempt, 0, from_other_families + from_own_family)
