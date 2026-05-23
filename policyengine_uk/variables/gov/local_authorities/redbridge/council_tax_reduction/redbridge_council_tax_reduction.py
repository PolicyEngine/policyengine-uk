from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_redbridge_working_age,
)


class redbridge_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Redbridge Council Tax Reduction"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.redbridge.council_tax_reduction
        local_authority = benunit.household("local_authority", period)
        country = benunit.household("country", period)
        has_pensioner = benunit.household(
            "council_tax_reduction_household_has_pensioner", period
        )
        working_age = is_redbridge_working_age(
            local_authority,
            country,
            has_pensioner,
        )
        person = benunit.members
        has_dependants = benunit.any(
            person("is_child_or_qualifying_young_person_for_child_benefit", period)
        )
        weekly_net_earnings = benunit(
            "redbridge_council_tax_reduction_weekly_net_earnings", period
        )
        in_remunerative_work = benunit(
            "redbridge_council_tax_reduction_claimant_in_remunerative_work", period
        )
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        contribution_based_benefit = (
            benunit.sum(
                person("is_adult", period)
                * ~person(
                    "is_child_or_qualifying_young_person_for_child_benefit", period
                )
                * (person("jsa_contrib", period) + person("esa_contrib", period))
            )
            > 0
        )
        has_uc_award = benunit("universal_credit", period) > 0
        not_working_passported = relevant_income_based_benefit | (
            (has_uc_award | contribution_based_benefit) & ~in_remunerative_work
        )
        disability_class = benunit(
            "redbridge_council_tax_reduction_disability_class", period
        )
        support_rate = select(
            [
                disability_class,
                has_dependants & not_working_passported,
                ~has_dependants & not_working_passported,
                has_dependants
                & in_remunerative_work
                & (weekly_net_earnings < ctr.earnings_threshold.with_dependants),
                ~has_dependants
                & in_remunerative_work
                & (weekly_net_earnings < ctr.earnings_threshold.without_dependants),
            ],
            [
                ctr.support_rate.disability,
                ctr.support_rate.not_working_with_dependants,
                ctr.support_rate.not_working_without_dependants,
                ctr.support_rate.working_with_dependants,
                ctr.support_rate.working_without_dependants,
            ],
            default=0,
        )
        liability = benunit.household("council_tax", period)
        non_dep_deductions = benunit(
            "redbridge_council_tax_reduction_non_dep_deductions", period
        )
        award = max_(0, liability * support_rate - non_dep_deductions)
        minimum_award = ctr.minimum_award.weekly_amount * WEEKS_IN_YEAR
        award = where(award < minimum_award, 0, award)
        capital_eligible = (
            benunit.household("savings", period) <= ctr.means_test.capital_limit
        )
        return (
            working_age
            * benunit("benunit_contains_household_head", period)
            * benunit("would_claim_council_tax_reduction", period)
            * capital_eligible
            * award
        )
