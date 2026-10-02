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
        # Limited capability for work and work-related activity
        has_lcwra = benunit.any(person("uc_limited_capability_for_WRA", period))

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

        # Working Tax Credit
        QUAL_BENUNIT_BENEFITS = [
            "working_tax_credit",  # If getting WTC, likely working enough
        ]

        qualifying_personal_benefits = add(benunit, period, QUAL_PERSONAL_BENEFITS)
        qualifying_benunit_benefits = add(benunit, period, QUAL_BENUNIT_BENEFITS)

        # Check for Armed Forces Compensation Scheme payments
        afcs = benunit("afcs", period) > 0

        # HB Regs 2006 reg 75F(1)(a), UC Regs 2013 reg 83(1)(a): "the claimant
        # or the claimant's partner is receiving an employment and support
        # allowance ... which includes a support component". Contributory and
        # income-related allowances both carry it; another member's allowance
        # does not count.
        claimant = person("is_claimant_or_partner", period)
        receiving_esa = (person("esa_contrib", period) > 0) | person(
            "is_on_income_related_esa", period
        )
        esa_support_component = benunit.any(
            claimant & receiving_esa & person("esa_includes_support_component", period)
        )

        return (
            has_lcwra
            | gets_uc_carer_element
            | (qualifying_personal_benefits > 0)
            | (qualifying_benunit_benefits > 0)
            | afcs
            | esa_support_component
        )
