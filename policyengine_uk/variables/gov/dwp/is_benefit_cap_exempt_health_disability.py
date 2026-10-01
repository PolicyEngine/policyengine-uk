from policyengine_uk.model_api import *


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

        # UC-specific exemptions
        # Limited capability for work and work-related activity: "the LCWRA
        # element is included in the award" (UC Regs 2013 reg. 83(1)(a)),
        # which it is only for a claimant (reg. 27(1)).
        has_lcwra = benunit("uc_LCWRA_element", period) > 0

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

        # Disability and carer benefits that exempt from cap. Whose receipt
        # exempts the award depends on the benefit (UC Regs 2013 reg. 83(1));
        # HB Regs 2006 reg. 75F(1) draws the same lines between the claimant
        # or partner and a child or young person.
        claimant = person("is_uc_assessed_claimant", period)
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_universal_credit", period
        )
        young_person = child_or_young_person & person(
            "is_qualifying_young_person_for_universal_credit", period
        )
        # "a claimant is receiving" (reg. 83(1)(b), (c))
        QUAL_CLAIMANT_BENEFITS = [
            "attendance_allowance",
            "iidb",  # Industrial injuries disability benefit
        ]
        # "a claimant, or a qualifying young person for whom a claimant is
        # responsible" (reg. 83(1)(g), (i), (ia))
        QUAL_CLAIMANT_OR_YOUNG_PERSON_BENEFITS = [
            "carers_allowance",
            "carer_support_payment",
            "pip_dl",  # PIP daily living component
            "pip_m",  # PIP mobility component
        ]
        # "a claimant, or a child or qualifying young person for whom a
        # claimant is responsible" (reg. 83(1)(f))
        QUAL_CLAIMANT_OR_CHILD_BENEFITS = [
            "dla",  # Disability Living Allowance (includes components)
        ]

        # ESA and Working Tax Credit
        QUAL_BENUNIT_BENEFITS = [
            "esa_income",  # Income-based ESA
            "working_tax_credit",  # If getting WTC, likely working enough
        ]

        qualifying_personal_benefits = (
            add_for_members(benunit, period, QUAL_CLAIMANT_BENEFITS, claimant)
            + add_for_members(
                benunit,
                period,
                QUAL_CLAIMANT_OR_YOUNG_PERSON_BENEFITS,
                claimant | young_person,
            )
            + add_for_members(
                benunit,
                period,
                QUAL_CLAIMANT_OR_CHILD_BENEFITS,
                claimant | child_or_young_person,
            )
        )
        qualifying_benunit_benefits = add(benunit, period, QUAL_BENUNIT_BENEFITS)

        # Check for Armed Forces Compensation Scheme payments: "a claimant is
        # receiving" (reg. 83(1)(e))
        afcs = add_for_members(benunit, period, ["afcs"], claimant) > 0

        # ESA contribution-based with support component: "the claimant is
        # receiving" (reg. 83(1)(a))
        esa_support_component = (
            add_for_members(benunit, period, ["esa_contrib"], claimant) > 0
        )

        return (
            has_lcwra
            | gets_uc_carer_element
            | (qualifying_personal_benefits > 0)
            | (qualifying_benunit_benefits > 0)
            | afcs
            | esa_support_component
        )
