from policyengine_uk.model_api import *


class forest_of_dean_council_tax_reduction_protected_group(Variable):
    value_type = bool
    entity = BenUnit
    label = "Forest of Dean claimant qualifies for the Class B protected scheme"
    documentation = "Class B (h) and (i) protect benefit units where the claimant, partner or a dependant receives one of: Armed Forces Independence Payment, Attendance Allowance, Disability Living Allowance, Employment and Support Allowance, Personal Independence Payment, Severe Disability Allowance, War Pension or War Widow's Pension, or the Work Capability Element of Universal Credit. War Pension/War Widow's Pension and the UC Work Capability Element are not modelled in PolicyEngine UK and are covered by Forest of Dean-scoped source inputs."
    definition_period = YEAR
    reference = "https://www.fdean.gov.uk/media/r4ff2lok/council-tax-support-scheme-for-working-age-customers-2026-to-2027.pdf"

    def formula(benunit, period, parameters):
        person = benunit.members
        # Any benunit member - claimant, partner or dependant - with a modelled
        # qualifying benefit makes the benunit Class B (paragraphs (h) and (i)).
        modelled_qualifying_benefit = (
            (person("armed_forces_independence_payment", period) > 0)
            | (person("attendance_allowance", period) > 0)
            | (person("dla", period) > 0)
            | (person("pip", period) > 0)
            | (person("sda", period) > 0)
        )
        any_member_qualifying = benunit.any(modelled_qualifying_benefit)
        # ESA at the benunit level (income or contributory).
        esa_qualifying = (benunit("esa_income", period) > 0) | (
            benunit("esa_contrib", period) > 0
        )
        # Source-input booleans for facts PolicyEngine UK does not model directly.
        war_pension = benunit(
            "forest_of_dean_council_tax_reduction_war_pension", period
        )
        uc_lcw_element = benunit(
            "forest_of_dean_council_tax_reduction_uc_lcw_element", period
        )
        return any_member_qualifying | esa_qualifying | war_pension | uc_lcw_element
