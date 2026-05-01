from policyengine_uk.model_api import *


class barking_and_dagenham_council_tax_reduction_weekly_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Barking and Dagenham CTS weekly net income"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
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
        standard_net_earnings = max_(0, gross_earnings - earnings_deductions)
        has_uc = benunit("universal_credit", period) > 0
        uc_earnings_deductions = benunit.sum(
            claimant_or_partner
            * (
                person("income_tax", period)
                + person("national_insurance", period)
                + person("pension_contributions", period)
            )
        )
        uc_net_earnings = max_(
            0,
            gross_earnings - uc_earnings_deductions,
        )
        net_earnings = where(has_uc, uc_net_earnings, standard_net_earnings)
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
        )
        unearned_income += add(
            benunit,
            period,
            [
                "tax_credits",
            ],
        )
        unearned_income += benunit(
            "barking_and_dagenham_council_tax_reduction_countable_universal_credit",
            period,
        )
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit",
            period,
        )
        annual_income = where(
            relevant_income_based_benefit,
            0,
            net_earnings + unearned_income,
        )
        return annual_income / WEEKS_IN_YEAR
