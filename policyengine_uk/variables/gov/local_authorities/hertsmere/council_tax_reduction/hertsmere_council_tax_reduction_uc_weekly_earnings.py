from policyengine_uk.model_api import *


class hertsmere_council_tax_reduction_uc_weekly_earnings(Variable):
    value_type = float
    entity = BenUnit
    label = "Hertsmere Class G Universal Credit weekly earnings"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.hertsmere.gov.uk/asset-library/cts-scheme-2026-27.pdf"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.hertsmere.council_tax_reduction
        person = benunit.members
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        claimant_or_partner = person("is_adult", period) & ~child_or_young_person
        gross_earnings = benunit.sum(
            claimant_or_partner
            * (
                person("employment_income", period)
                + person("self_employment_income", period)
            )
        )
        earnings_deductions = benunit.sum(
            claimant_or_partner
            * (
                person("income_tax", period)
                + person("national_insurance", period)
                + person("pension_contributions", period) * 0.5
            )
        )
        net_earnings = max_(0, gross_earnings - earnings_deductions)
        is_lone_parent = benunit("is_lone_parent", period)
        is_couple = benunit("is_couple", period)
        protected = benunit("hertsmere_council_tax_reduction_protected_group", period)
        weekly_hours = benunit.max(claimant_or_partner * person("weekly_hours", period))
        weekly_disregard = select(
            [is_lone_parent, protected, is_couple],
            [
                ctr.earnings_disregard.lone_parent,
                ctr.earnings_disregard.disabled_or_support_component,
                ctr.earnings_disregard.couple,
            ],
            default=ctr.earnings_disregard.single,
        )
        weekly_net_earnings = net_earnings / WEEKS_IN_YEAR
        adult_age = benunit.max(claimant_or_partner * person("age", period))
        has_family = benunit.any(child_or_young_person)
        disability_component = (
            (benunit("disability_premium", period) > 0)
            | (benunit("severe_disability_premium", period) > 0)
            | (benunit("enhanced_disability_premium", period) > 0)
            | (
                benunit("hertsmere_council_tax_reduction_esa_support_component", period)
                > 0
            )
            | benunit.any(
                claimant_or_partner & person("uc_limited_capability_for_WRA", period)
            )
        )
        source_wtc_condition = benunit(
            "hertsmere_council_tax_reduction_source_additional_earnings_disregard",
            period,
        )
        additional_condition = (
            source_wtc_condition
            | ((adult_age >= 25) & (weekly_hours >= 30))
            | (is_couple & has_family & (weekly_hours >= 16))
            | (is_lone_parent & (weekly_hours >= 16))
            | (disability_component & (weekly_hours >= 16))
        )
        additional_available = weekly_net_earnings >= (
            weekly_disregard + ctr.earnings_disregard.additional_working
        )
        additional_disregard = (
            additional_condition & additional_available
        ) * ctr.earnings_disregard.additional_working
        countable_earnings = max_(
            0,
            net_earnings - (weekly_disregard + additional_disregard) * WEEKS_IN_YEAR,
        )
        return countable_earnings / WEEKS_IN_YEAR
