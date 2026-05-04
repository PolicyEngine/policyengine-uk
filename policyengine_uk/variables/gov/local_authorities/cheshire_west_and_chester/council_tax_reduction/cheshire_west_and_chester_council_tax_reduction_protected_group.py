from policyengine_uk.model_api import *


class cheshire_west_and_chester_council_tax_reduction_protected_group(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether the Cheshire West and Chester CTR claimant is in protected Classes C or D"
    definition_period = YEAR
    reference = "https://www.cheshirewestandchester.gov.uk/asset-library/council-tax-reduction-summary-2026-2027-annex-a-part-2.pdf"

    def formula(benunit, period, parameters):
        person = benunit.members
        claimant_or_partner = person("is_adult", period)
        lcwra = benunit.any(
            claimant_or_partner & person("uc_limited_capability_for_WRA", period)
        )
        disabled_child = benunit.any(
            ~person("is_adult", period) & person("is_disabled_for_benefits", period)
        )
        disabled_child_premium = (
            disabled_child
            | (benunit("CTC_disabled_child_element", period) > 0)
            | (benunit("uc_disability_elements", period) > 0)
        )
        source_protected = benunit(
            "cheshire_west_and_chester_council_tax_reduction_source_protected_group",
            period,
        )
        return (
            lcwra
            | (benunit("carer_premium", period) > 0)
            | disabled_child_premium
            | (benunit("severe_disability_premium", period) > 0)
            | (benunit("enhanced_disability_premium", period) > 0)
            | source_protected
        )
