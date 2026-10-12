from policyengine_uk.model_api import *
from policyengine_uk.utils.uc_work_related_requirements import (
    other_member_of_single_claim_in_shared_rules,
)
from policyengine_uk.utils.benefit_unit import add_for_members


class is_benefit_cap_exempt_health_disability(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether exempt from the benefits cap because of health or disability"
    definition_period = YEAR
    reference = "https://www.gov.uk/benefit-cap/when-youre-not-affected"

    def formula(benunit, period, parameters):
        person = benunit.members

        # The exceptions read "a claimant" (UC Regs 2013 reg. 83(1)). A
        # partner who cannot be a joint claimant, so that the other member
        # claims Universal Credit as a single person (reg. 3(3)), is not a
        # claimant: their own disability benefits and limited capability do
        # not lift the cap.
        not_a_claimant = other_member_of_single_claim_in_shared_rules(person, period)

        # Limited capability for work and work-related activity
        has_lcwra = benunit.any(
            person("uc_limited_capability_for_WRA", period) & ~not_a_claimant
        )

        # Carer element in UC indicates caring for someone with disability
        gets_uc_carer_element = benunit("uc_carer_element", period) > 0

        # Disability and carer benefits that exempt from cap
        QUAL_PERSONAL_BENEFITS = [
            "attendance_allowance",
            # Entitlement, not payment: HB Regs 2006 reg 75F(1)(h)-(ha) and UC
            # Regs 2013 reg 83(1)(i)-(ia) exempt a person "entitled to" Carer's
            # Allowance or Carer Support Payment, even if an overlapping benefit
            # reduces it to nil.
            "is_entitled_to_carer_benefit",
            "dla",  # Disability Living Allowance (includes components)
            "pip_dl",  # PIP daily living component
            "pip_m",  # PIP mobility component
            "iidb",  # Industrial injuries disability benefit
        ]

        # ESA and Working Tax Credit
        QUAL_BENUNIT_BENEFITS = [
            "esa_income",  # Income-based ESA
            "working_tax_credit",  # If getting WTC, likely working enough
        ]

        qualifying_personal_benefits = add_for_members(
            benunit, period, QUAL_PERSONAL_BENEFITS, ~not_a_claimant
        )
        qualifying_benunit_benefits = add(benunit, period, QUAL_BENUNIT_BENEFITS)

        # Armed Forces Independence Payment counts only for the people the
        # regulations name. Housing Benefit: "the claimant, the claimant's
        # partner or a young person for whom the claimant or the claimant's
        # partner is responsible" (HB Regs 2006 reg 75F(1)(ea)), so not a
        # child under 16. Universal Credit: AFIP is within "attendance
        # allowance" (UC Regs 2013 reg 2), which excepts only where "a
        # claimant is receiving" it (reg 83(1)(c)). The model applies one
        # cap to both schemes, so the claimant, partner or a Housing Benefit
        # young person counts.
        housing_benefit_young_person = person(
            "is_child_or_young_person_for_legacy_benefits", period
        ) & person("is_qualifying_young_person_for_child_benefit", period)
        afip_counted = (
            person("is_claimant_or_partner", period) & ~not_a_claimant
        ) | housing_benefit_young_person
        afip = (
            add_for_members(
                benunit, period, ["armed_forces_independence_payment"], afip_counted
            )
            > 0
        )

        # Check for Armed Forces Compensation Scheme payments
        afcs = add_for_members(benunit, period, ["afcs"], ~not_a_claimant) > 0

        # ESA contribution-based with support component
        esa_support_component = (
            add_for_members(benunit, period, ["esa_contrib"], ~not_a_claimant) > 0
        )

        return (
            has_lcwra
            | gets_uc_carer_element
            | (qualifying_personal_benefits > 0)
            | (qualifying_benunit_benefits > 0)
            | afip
            | afcs
            | esa_support_component
        )
