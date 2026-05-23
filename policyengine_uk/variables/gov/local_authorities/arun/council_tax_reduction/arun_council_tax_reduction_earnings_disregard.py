from policyengine_uk.model_api import *


class arun_council_tax_reduction_earnings_disregard(Variable):
    value_type = float
    entity = BenUnit
    label = "Arun Council Tax Reduction earnings disregard"
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.arun.gov.uk/download.cfm?doc=docm93jijm4n20657.pdf&ver=27819"
    )

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.arun.council_tax_reduction
        has_uc_award = benunit("universal_credit", period) > 0
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
                + person("statutory_sick_pay", period)
                + person("statutory_maternity_pay", period)
                + person("statutory_paternity_pay", period)
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
        has_earnings = gross_earnings > 0
        disability_or_carer = benunit.any(
            claimant_or_partner
            & (
                person("is_disabled_for_benefits", period)
                | (person("carers_allowance", period) > 0)
                | (person("armed_forces_independence_payment", period) > 0)
            )
        ) | (benunit("uc_carer_element", period) > 0)
        weekly_disregard = select(
            [
                benunit("is_lone_parent", period),
                disability_or_carer,
                benunit("is_couple", period),
            ],
            [
                ctr.earnings_disregard.lone_parent,
                ctr.earnings_disregard.disability_or_carer,
                ctr.earnings_disregard.couple,
            ],
            default=ctr.earnings_disregard.standard,
        )
        weekly_hours = benunit.max(claimant_or_partner * person("weekly_hours", period))
        weekly_net_earnings = max_(0, gross_earnings - earnings_deductions) / (
            WEEKS_IN_YEAR
        )
        childcare_deduction = (
            benunit("arun_council_tax_reduction_childcare_deduction", period)
            / WEEKS_IN_YEAR
        )
        adult_age = benunit.max(claimant_or_partner * person("age", period))
        has_family = benunit.any(child_or_young_person)
        disability_component = (
            (benunit("disability_premium", period) > 0)
            | (benunit("severe_disability_premium", period) > 0)
            | (benunit("enhanced_disability_premium", period) > 0)
            | benunit.any(
                claimant_or_partner & person("uc_limited_capability_for_WRA", period)
            )
        )
        source_wtc_condition = benunit(
            "arun_council_tax_reduction_source_additional_earnings_disregard",
            period,
        )
        additional_condition = (
            source_wtc_condition
            | ((adult_age >= 25) & (weekly_hours >= 30))
            | (benunit("is_couple", period) & has_family & (weekly_hours >= 16))
            | (benunit("is_lone_parent", period) & (weekly_hours >= 16))
            | (disability_component & (weekly_hours >= 16))
        )
        additional_available = weekly_net_earnings >= (
            weekly_disregard
            + childcare_deduction
            + ctr.earnings_disregard.additional_working
        )
        additional_disregard = (
            additional_condition & additional_available
        ) * ctr.earnings_disregard.additional_working
        return (
            ~has_uc_award
            * has_earnings
            * (weekly_disregard + additional_disregard)
            * WEEKS_IN_YEAR
        )
