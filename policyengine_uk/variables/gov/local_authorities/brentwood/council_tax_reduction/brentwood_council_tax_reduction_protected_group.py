from policyengine_uk.model_api import *


class brentwood_council_tax_reduction_protected_group(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether the benefit unit qualifies for Brentwood's Schedule 1 paragraph 3 protected-group 100 percent uplift"
    documentation = "Schedule 1 paragraph 3 uplifts the band discount to 100 percent where the applicant, partner or any dependant in their household is entitled to: Disability Living Allowance, Personal Independence Payment, Attendance Allowance, Universal Credit with the Limited Capability for Work or Limited Capability for Work Related Activity element, Armed Forces Independence Payment, Working Tax Credit with the disability element, Severe Disablement Allowance, or Employment and Support Allowance with the support component. The UC LCW element, the WTC disability element and the ESA Support Component are not modeled directly in PolicyEngine UK, so jurisdiction-scoped Brentwood source-input booleans are provided for those facts."
    definition_period = YEAR
    reference = "https://www.brentwood.gov.uk/sites/default/files/2026-03/Council%20Tax%20reduction%20scheme%20S13A%202026-27%20FINAL.pdf"

    def formula(benunit, period, parameters):
        person = benunit.members
        # Source covers the applicant, partner, and dependants, not non-dependants.
        dla = benunit.sum(person("dla_sc", period) + person("dla_m", period))
        pip = benunit.sum(person("pip_dl", period) + person("pip_m", period))
        attendance = benunit.sum(person("attendance_allowance", period))
        afip = benunit.sum(person("armed_forces_independence_payment", period))
        sda = benunit.sum(person("sda", period))
        # UC LCWRA element is modeled directly in PolicyEngine UK.
        uc_lcwra = benunit("uc_LCWRA_element", period)
        # UC LCW element, WTC disability element and ESA Support Component are
        # not modeled in PolicyEngine UK; Brentwood-scoped source inputs let
        # households assert receipt of those elements for the protected-group
        # uplift.
        uc_lcw = benunit("brentwood_council_tax_reduction_uc_lcw_element", period)
        wtc_disability = benunit(
            "brentwood_council_tax_reduction_wtc_disability_element", period
        )
        esa_support = benunit(
            "brentwood_council_tax_reduction_esa_support_component", period
        )
        return (
            (dla > 0)
            | (pip > 0)
            | (attendance > 0)
            | (afip > 0)
            | (sda > 0)
            | (uc_lcwra > 0)
            | uc_lcw
            | wtc_disability
            | esa_support
        )
