from policyengine_uk.model_api import *


class hartlepool_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Hartlepool Council Tax Reduction"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.hartlepool.gov.uk/downloads/file/1484/hbc-council-tax-reduction-scheme-2026-27"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.hartlepool.council_tax_reduction
        local_scheme = benunit(
            "hartlepool_council_tax_reduction_is_local_scheme", period
        )
        weekly_income = benunit(
            "hartlepool_council_tax_reduction_weekly_income", period
        )
        person = benunit.members
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        dependant_count = benunit.sum(child_or_young_person)
        is_couple = benunit("is_couple", period)
        band = ctr.income_band
        support_rate = select(
            [
                ~is_couple & (dependant_count == 0),
                ~is_couple & (dependant_count == 1),
                ~is_couple & (dependant_count >= 2),
                is_couple & (dependant_count == 0),
                is_couple & (dependant_count == 1),
                is_couple & (dependant_count >= 2),
            ],
            [
                band.single.calc(weekly_income),
                band.single_one_dependant.calc(weekly_income),
                band.single_two_or_more_dependants.calc(weekly_income),
                band.couple.calc(weekly_income),
                band.couple_one_dependant.calc(weekly_income),
                band.couple_two_or_more_dependants.calc(weekly_income),
            ],
            default=0,
        )
        income_based_benefit = (
            (benunit("income_support", period) > 0)
            | (benunit("jsa_income", period) > 0)
            | (benunit("esa_income", period) > 0)
        )
        support_rate = where(income_based_benefit, 0.9, support_rate)
        liability = benunit.household("council_tax", period)
        non_dep_deductions = benunit(
            "hartlepool_council_tax_reduction_non_dep_deductions", period
        )
        award = max_(0, liability * support_rate - non_dep_deductions)
        has_uc_award = (
            max_(
                benunit("universal_credit_pre_benefit_cap", period),
                benunit("universal_credit", period),
            )
            > 0
        )
        non_uc_capital_eligible = (
            benunit.household("savings", period) <= ctr.means_test.capital_limit
        )
        uc_capital_eligible = (
            benunit("uc_assessable_capital", period) <= ctr.means_test.capital_limit
        )
        capital_eligible = where(
            has_uc_award, uc_capital_eligible, non_uc_capital_eligible
        )
        return (
            local_scheme
            * benunit("benunit_contains_household_head", period)
            * benunit("would_claim_council_tax_reduction", period)
            * capital_eligible
            * award
        )
