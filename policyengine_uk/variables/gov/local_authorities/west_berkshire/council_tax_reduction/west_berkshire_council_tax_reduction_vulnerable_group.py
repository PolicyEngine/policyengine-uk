from policyengine_uk.model_api import *


class west_berkshire_council_tax_reduction_vulnerable_group(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether the benefit unit falls within West Berkshire's paragraph 29D protected vulnerable category"
    documentation = "Paragraph 29D places a working-age applicant in the Class E1 protected vulnerable category where the claimant or partner is entitled to Disability Premium, Enhanced Disability Premium, Severe Disability Premium, or Disabled Child Premium (Schedule 3 paragraphs 9-13), or is in receipt of any component of Employment and Support Allowance, any amount of War Pension, or the UC Limited Capability for Work element. PolicyEngine UK has the four disability premiums as benunit variables and ESA via the esa wrapper; the LCW element, the War Pension, and the Disabled Child Premium are not separately modeled, so jurisdiction-scoped Brentwood-style Boolean source inputs are provided. The vulnerable category is keyed off the claimant or partner only, not non-dependants."
    definition_period = YEAR
    reference = "https://www.westberks.gov.uk/media/66425/Council-Tax-Reduction-Scheme-2026-27/pdf/The_Council_Tax_Reduction_Scheme_as_amended_by_West_Berkshire_Council_2026.pdf"

    def formula(benunit, period, parameters):
        disability_premium = benunit("disability_premium", period)
        enhanced_disability_premium = benunit("enhanced_disability_premium", period)
        severe_disability_premium = benunit("severe_disability_premium", period)
        disabled_child_premium = benunit(
            "west_berkshire_council_tax_reduction_disabled_child_premium", period
        )
        esa_any_component = benunit("esa", period)
        war_pension = benunit(
            "west_berkshire_council_tax_reduction_war_pension", period
        )
        uc_lcwra = benunit("uc_LCWRA_element", period)
        uc_lcw = benunit("west_berkshire_council_tax_reduction_uc_lcw_element", period)
        return (
            (disability_premium > 0)
            | (enhanced_disability_premium > 0)
            | (severe_disability_premium > 0)
            | disabled_child_premium
            | (esa_any_component > 0)
            | war_pension
            | (uc_lcwra > 0)
            | uc_lcw
        )
