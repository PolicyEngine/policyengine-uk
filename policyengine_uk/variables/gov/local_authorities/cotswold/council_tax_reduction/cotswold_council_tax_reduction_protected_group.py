from policyengine_uk.model_api import *


class cotswold_council_tax_reduction_protected_group(Variable):
    value_type = bool
    entity = BenUnit
    label = "Cotswold Council Tax Support protected group"
    definition_period = YEAR
    reference = "https://cotswold.gov.uk/media/k04l1hc2/cdc-cts-scheme-2026-27.pdf"

    def formula(benunit, period, parameters):
        person = benunit.members
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        claimant_or_partner = person("is_adult", period) & ~child_or_young_person
        disability_premium = (
            benunit("disability_premium", period)
            + benunit("severe_disability_premium", period)
            + benunit("enhanced_disability_premium", period)
        )
        esa_any_rate = (benunit("esa_income", period) > 0) | benunit.any(
            claimant_or_partner & (person("esa_contrib", period) > 0)
        )
        adult_protected_benefit = benunit.any(
            claimant_or_partner
            & (
                (person("armed_forces_independence_payment", period) > 0)
                | person("uc_limited_capability_for_WRA", period)
            )
        )
        source_protected = benunit(
            "cotswold_council_tax_reduction_source_protected_group", period
        )
        return (
            (disability_premium > 0)
            | esa_any_rate
            | adult_protected_benefit
            | source_protected
        )
