from policyengine_uk.model_api import *


class bassetlaw_council_tax_reduction_earnings_disregard(Variable):
    value_type = float
    entity = BenUnit
    label = "Bassetlaw Council Tax Reduction earnings disregard"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.bassetlaw.gov.uk/media/15ehht0s/council-tax-reduction-scheme-working-age-2026-2027.pdf"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.bassetlaw.council_tax_reduction
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
        disability_or_carer = (
            (benunit("disability_premium", period) > 0)
            | (benunit("severe_disability_premium", period) > 0)
            | (benunit("enhanced_disability_premium", period) > 0)
            | (benunit("carers_allowance", period) > 0)
        )
        base_weekly = select(
            [
                benunit("is_lone_parent", period),
                disability_or_carer,
                benunit("is_couple", period),
            ],
            [
                ctr.earnings_disregard.lone_parent,
                ctr.earnings_disregard.disabled_or_carer,
                ctr.earnings_disregard.couple,
            ],
            default=ctr.earnings_disregard.single,
        )
        weekly_hours = benunit.max(claimant_or_partner * person("weekly_hours", period))
        weekly_net_earnings = (
            max_(0, gross_earnings - earnings_deductions) / WEEKS_IN_YEAR
        )
        childcare_deduction = benunit(
            "bassetlaw_council_tax_reduction_childcare_deduction", period
        )
        worker_addition_available = weekly_net_earnings >= (
            base_weekly
            + childcare_deduction / WEEKS_IN_YEAR
            + ctr.earnings_disregard.worker_addition
        )
        works_qualifying_hours = (
            (weekly_hours >= 30)
            | (
                (benunit("is_lone_parent", period) | benunit("is_couple", period))
                & (weekly_hours >= 16)
            )
            | (disability_or_carer & (weekly_hours >= 16))
        )
        worker_addition = (
            works_qualifying_hours & worker_addition_available
        ) * ctr.earnings_disregard.worker_addition
        return (gross_earnings > 0) * (base_weekly + worker_addition) * WEEKS_IN_YEAR
