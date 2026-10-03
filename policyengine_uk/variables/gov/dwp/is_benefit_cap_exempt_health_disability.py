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
        # Check if anyone in benefit unit is over state pension age
        person = benunit.members
        over_pension_age = person("is_SP_age", period)
        has_pensioner = benunit.any(over_pension_age)

        # The exceptions read "a claimant" (UC Regs 2013 reg. 83(1)). A
        # partner who cannot be a joint claimant, so that the other member
        # claims Universal Credit as a single person (reg. 3(3)), is not a
        # claimant: their own disability benefits and limited capability do
        # not lift the cap.
        not_a_claimant = other_member_of_single_claim_in_shared_rules(person, period)

        # UC-specific exemptions
        # Limited capability for work and work-related activity
        has_lcwra = benunit.any(
            person("uc_limited_capability_for_WRA", period) & ~not_a_claimant
        )

        # Carer element in UC indicates caring for someone with disability
        gets_uc_carer_element = benunit("uc_carer_element", period) > 0

        # Earnings exemption for UC (£846/month = £10,152/year)
        # Note: Only check earned income, not UC amount itself to avoid circular dependency
        uc_earned = benunit.sum(
            benunit.members("employment_income", period)
            + benunit.members("self_employment_income", period)
            - benunit.members("income_tax", period)
            - benunit.members("national_insurance", period)
        )
        earnings_threshold = 10_152
        meets_earnings_test = uc_earned >= earnings_threshold

        # Disability and carer benefits that exempt from cap
        QUAL_PERSONAL_BENEFITS = [
            "attendance_allowance",
            "carers_allowance",
            "carer_support_payment",
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
            | afcs
            | esa_support_component
        )
