from policyengine_uk.model_api import *


class uc_non_dep_deductions(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit non-dependent deductions"
    documentation = (
        "Housing cost contributions for the renter's non-dependants. Those in "
        "other families of the household count in one claim, the one "
        "uc_non_dependants_counted picks (the household head's family if it "
        "claims, otherwise the first claiming sharer). Those within a "
        "renter's own benefit unit count in that family's claim if it makes "
        "one, otherwise in the same counted claim. Making a claim is the "
        "model's claims_universal_credit flag for a renting, UC-eligible "
        "family, so a family flagged as claiming counts its own non-dependants "
        "even where its award is nil. None if the renter or a joint renter is "
        "exempt."
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
        # Non-dependants from other families are not liable for rent (para
        # 9(2)(d)), and each counts in one Universal Credit claim only (para
        # 9(2)(f)): see uc_non_dependants_counted.
        other_family = person("is_non_dependant_of_household_head", period)
        # A member of a renter's own benefit unit who is not the claimant,
        # partner or a qualifying young person is a non-dependant of that
        # renter (para 9(1)(c) and (2)(a), (g)). Their own family's claim
        # counts them if it makes one; otherwise the claim that counts the
        # household's other non-dependants does (para 9(2)(f)).
        in_unit = (
            person("is_benefit_unit_non_dependant_for_universal_credit", period)
            & ~other_family
        )
        own_claim = (
            benunit("benunit_is_rent_liable", period)
            & benunit("is_uc_eligible", period)
            & benunit("claims_universal_credit", period)
        )
        to_own_claim = in_unit & benunit.project(own_claim)
        counted = benunit("uc_non_dependants_counted", period)
        from_household = counted * benunit.max(
            person.household.sum(
                deductions * ((other_family | in_unit) & ~to_own_claim)
            )
        )
        from_own_family = benunit.sum(deductions * to_own_claim)
        # Sch 4 para 15: no contribution for any non-dependant where the
        # renter, or either joint renter, is blind or receives a qualifying
        # disability benefit.
        renter_exempt = benunit("uc_non_dep_deductions_renter_exempt", period)
        return where(renter_exempt, 0, from_household + from_own_family)
