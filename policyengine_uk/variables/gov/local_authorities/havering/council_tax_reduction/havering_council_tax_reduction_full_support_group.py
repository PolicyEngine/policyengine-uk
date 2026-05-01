from policyengine_uk.model_api import *


class havering_council_tax_reduction_full_support_group(Variable):
    value_type = bool
    entity = BenUnit
    label = "Havering CTS 100 percent support group"
    definition_period = YEAR
    reference = "https://www.havering.gov.uk/downloads/file/6930/council-tax-support-scheme-2025-2026"

    def formula(benunit, period, parameters):
        person = benunit.members
        claimant_or_partner = person("is_adult", period)
        care_leaver = benunit.any(
            claimant_or_partner
            & person("havering_council_tax_reduction_care_leaver", period)
        )
        war_pension = benunit(
            "havering_council_tax_reduction_war_pension_protected", period
        )
        return care_leaver | war_pension
