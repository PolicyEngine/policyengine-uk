from policyengine_uk.model_api import *


class harrow_council_tax_reduction_disabled(Variable):
    value_type = bool
    entity = BenUnit
    label = "Harrow CTS working-age disabled group"
    definition_period = YEAR
    reference = "https://www.harrow.gov.uk/downloads/file/33606/council-tax-support-scheme-2026-27"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.harrow.council_tax_reduction
        person = benunit.members
        claimant_or_partner = person("is_adult", period)
        earned_income = person("employment_income", period) + person(
            "self_employment_income", period
        )
        claimant_partner_weekly_earnings = (
            benunit.sum(claimant_or_partner * earned_income) / WEEKS_IN_YEAR
        )
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        adult_disabled = benunit.any(
            claimant_or_partner
            & (
                person("is_disabled_for_benefits", period)
                | (person("pip", period) > 0)
                | (person("dla", period) > 0)
                | person("is_blind", period)
                | (person("incapacity_benefit", period) > 0)
                | person("uc_limited_capability_for_WRA", period)
            )
        )
        disabled_child = benunit.any(
            child_or_young_person
            & (
                person("is_disabled_for_benefits", period)
                | (person("pip", period) > 0)
                | (person("dla", period) > 0)
            )
        )
        local_disabled_marker = benunit(
            "harrow_council_tax_reduction_war_pension_protected", period
        ) | benunit.household(
            "harrow_council_tax_reduction_disabled_band_reduction", period
        )
        disabled = adult_disabled | disabled_child | local_disabled_marker
        return disabled & (
            claimant_partner_weekly_earnings < ctr.disabled.earnings_limit
        )
