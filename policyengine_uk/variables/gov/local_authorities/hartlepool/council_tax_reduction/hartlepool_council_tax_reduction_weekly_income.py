from policyengine_uk.model_api import *


class hartlepool_council_tax_reduction_weekly_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Hartlepool Council Tax Reduction weekly net income"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.hartlepool.gov.uk/downloads/file/1484/hbc-council-tax-reduction-scheme-2026-27"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.hartlepool.council_tax_reduction
        has_uc_award = (
            max_(
                benunit("universal_credit_pre_benefit_cap", period),
                benunit("universal_credit", period),
            )
            > 0
        )
        person = benunit.members
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        claimant_or_partner = person("is_adult", period) & ~child_or_young_person
        earnings = benunit.sum(
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
        net_earnings = max_(0, earnings - earnings_deductions)
        unearned_income = benunit.sum(
            claimant_or_partner
            * add(
                person,
                period,
                [
                    "property_income",
                    "private_pension_income",
                    "savings_interest_income",
                    "dividend_income",
                    "state_pension",
                    "carers_allowance",
                    "esa_contrib",
                    "jsa_contrib",
                    "maternity_allowance",
                    "statutory_sick_pay",
                    "statutory_maternity_pay",
                    "ssmg",
                    "miscellaneous_income",
                ],
            )
        ) + add(benunit, period, ["tax_credits"])
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        non_uc_weekly_income = max_(
            0,
            (net_earnings + unearned_income) / WEEKS_IN_YEAR
            - ctr.earnings_disregard.amount,
        )
        non_uc_weekly_income = where(
            relevant_income_based_benefit, 0, non_uc_weekly_income
        )
        uc_income = (
            benunit("uc_earned_income", period)
            + benunit("uc_unearned_income", period)
            + benunit("universal_credit", period)
        )
        uc_weekly_income = uc_income / WEEKS_IN_YEAR
        return where(has_uc_award, uc_weekly_income, non_uc_weekly_income)
