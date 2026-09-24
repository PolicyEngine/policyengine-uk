from policyengine_uk.model_api import *


class is_benefit_cap_exempt_health_disability(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether exempt from the benefits cap because of health or disability"
    definition_period = YEAR
    reference = "https://www.gov.uk/benefit-cap/when-youre-not-affected"

    def formula(benunit, period, parameters):
        person = benunit.members

        # Limited capability for work and work-related activity
        has_lcwra = benunit.any(person("uc_limited_capability_for_WRA", period))

        # Carer element in UC indicates caring for someone with disability
        gets_uc_carer_element = benunit("uc_carer_element", period) > 0

        # Disability and carer benefits that exempt from cap
        QUAL_PERSONAL_BENEFITS = [
            "attendance_allowance",
            "carers_allowance",
            "carer_support_payment",
            "dla",  # Disability Living Allowance (includes components)
            "pip_dl",  # PIP daily living component
            "pip_m",  # PIP mobility component
            "iidb",  # Industrial injuries disability benefit
            # Armed Forces Independence Payment is a statutory exemption
            "armed_forces_independence_payment",
        ]

        # ESA and Working Tax Credit
        QUAL_BENUNIT_BENEFITS = [
            "esa_income",  # Income-based ESA
            "working_tax_credit",  # If getting WTC, likely working enough
        ]

        qualifying_personal_benefits = add(benunit, period, QUAL_PERSONAL_BENEFITS)
        qualifying_benunit_benefits = add(benunit, period, QUAL_BENUNIT_BENEFITS)

        # Check for Armed Forces Compensation Scheme payments
        afcs = benunit("afcs", period) > 0

        # ESA contribution-based with support component
        esa_support_component = benunit("esa_contrib", period) > 0

        return (
            has_lcwra
            | gets_uc_carer_element
            | (qualifying_personal_benefits > 0)
            | (qualifying_benunit_benefits > 0)
            | afcs
            | esa_support_component
        )
