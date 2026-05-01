from policyengine_uk.model_api import *


class bury_council_tax_reduction_protected_group(Variable):
    value_type = bool
    entity = BenUnit
    label = "Bury CTR Band B cap protected group"
    definition_period = YEAR
    reference = (
        "https://www.bury.gov.uk/asset-library/bury-cts-scheme-policy-2026-27.pdf"
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        claimant_or_partner = person("is_adult", period)
        disability_or_carer_benefit = benunit.any(
            claimant_or_partner
            & (
                (person("attendance_allowance", period) > 0)
                | (person("dla", period) > 0)
                | (person("pip_dl", period) > 0)
                | (person("pip_m", period) > 0)
                | (person("carers_allowance", period) > 0)
            )
        )
        esa_support_component = benunit("esa_contrib", period) > 0
        armed_forces_compensation = benunit("afcs", period) > 0
        war_pension = benunit(
            "bury_council_tax_reduction_war_pension_protected", period
        )
        underlying_carer = benunit(
            "bury_council_tax_reduction_underlying_carer_protected", period
        )
        recent_bereavement = benunit(
            "bury_council_tax_reduction_bereavement_protected", period
        )
        lone_parent_with_child_under_5 = benunit("is_lone_parent", period) & (
            benunit("youngest_child_age", period) < 5
        )
        return benunit("benunit_contains_household_head", period) & (
            disability_or_carer_benefit
            | esa_support_component
            | armed_forces_compensation
            | war_pension
            | underlying_carer
            | lone_parent_with_child_under_5
            | recent_bereavement
        )
