from policyengine_uk.model_api import *


class ealing_council_tax_reduction_protected(Variable):
    value_type = bool
    entity = BenUnit
    label = "Ealing CTR protected working-age class"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        person = benunit.members
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        claimant_or_partner = person("is_adult", period) & ~child_or_young_person
        disability_or_carer = benunit.any(
            claimant_or_partner
            & (
                (person("dla", period) > 0)
                | (person("pip", period) > 0)
                | (person("attendance_allowance", period) > 0)
                | (person("carers_allowance", period) > 0)
                | (person("armed_forces_independence_payment", period) > 0)
            )
        )
        employment_and_support_allowance = benunit("esa", period) > 0
        uc_protected = benunit.any(
            claimant_or_partner & person("uc_limited_capability_for_WRA", period)
        ) | (
            add(
                benunit,
                period,
                [
                    "uc_disability_elements",
                    "uc_carer_element",
                ],
            )
            > 0
        )
        underlying_carer = benunit.any(
            claimant_or_partner
            & person(
                "ealing_council_tax_reduction_underlying_carers_allowance_entitlement",
                period,
            )
        )
        care_leaver_under_25 = benunit.any(
            claimant_or_partner
            & person("ealing_council_tax_reduction_care_leaver", period)
            & (person("age", period) < 25)
        )
        lone_parent_with_child_under_5 = benunit("is_lone_parent", period) & (
            benunit("youngest_child_age", period) < 5
        )
        return (
            disability_or_carer
            | employment_and_support_allowance
            | uc_protected
            | underlying_carer
            | care_leaver_under_25
            | lone_parent_with_child_under_5
        )
