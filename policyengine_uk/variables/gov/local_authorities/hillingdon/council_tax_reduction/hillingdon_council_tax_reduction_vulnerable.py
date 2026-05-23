from policyengine_uk.model_api import *


class hillingdon_council_tax_reduction_vulnerable(Variable):
    value_type = bool
    entity = BenUnit
    label = "Hillingdon CTR vulnerable Band 2 group"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        person = benunit.members
        claimant_or_partner = person("is_adult", period)
        claimant_partner_or_child = claimant_or_partner | person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        disability_benefit = benunit.any(
            claimant_partner_or_child
            & (
                (person("dla", period) > 0)
                | (person("pip", period) > 0)
                | (person("attendance_allowance", period) > 0)
            )
        )
        claimant_partner_disability_or_carer = benunit.any(
            claimant_or_partner
            & (
                person("is_blind", period)
                | (person("carers_allowance", period) > 0)
                | (person("armed_forces_independence_payment", period) > 0)
            )
        )
        uc_limited_capability = benunit.any(
            claimant_or_partner & person("uc_limited_capability_for_WRA", period)
        )
        disabled_child_uc_element = benunit("uc_disability_elements", period) > 0
        return (
            disability_benefit
            | claimant_partner_disability_or_carer
            | uc_limited_capability
            | disabled_child_uc_element
        )
