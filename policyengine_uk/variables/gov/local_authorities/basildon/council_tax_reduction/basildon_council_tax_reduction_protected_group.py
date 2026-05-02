from policyengine_uk.model_api import *


class basildon_council_tax_reduction_protected_group(Variable):
    value_type = bool
    entity = BenUnit
    label = "Basildon CTR protected group"
    definition_period = YEAR
    reference = "https://www.basildon.gov.uk/media/11563/Basildon-Council-Council-Tax-Reduction-Scheme-2026-27/pdf/Basildon_S13A_202627_Final.pdf?m=1771316212763"

    def formula(benunit, period, parameters):
        person = benunit.members
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        claimant_partner_or_dependant = (
            person("is_adult", period) | child_or_young_person
        )
        modeled_benefit = (
            (person("dla", period) > 0)
            | (person("pip", period) > 0)
            | (person("attendance_allowance", period) > 0)
            | (person("armed_forces_independence_payment", period) > 0)
            | person("uc_limited_capability_for_WRA", period)
        )
        source_protected = benunit(
            "basildon_council_tax_reduction_source_protected_group", period
        )
        esa_support_component = benunit(
            "basildon_council_tax_reduction_esa_support_component", period
        )
        wtc_disability = benunit(
            "basildon_council_tax_reduction_working_tax_credit_disability_element",
            period,
        )
        severe_disablement = benunit(
            "basildon_council_tax_reduction_severe_disablement_allowance", period
        )
        return (
            benunit.any(claimant_partner_or_dependant & modeled_benefit)
            | (esa_support_component > 0)
            | wtc_disability
            | (severe_disablement > 0)
            | source_protected
        )
