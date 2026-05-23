from policyengine_uk.model_api import *


class cheltenham_council_tax_reduction_weekly_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Cheltenham Council Tax Support weekly income"
    definition_period = YEAR
    unit = GBP
    reference = "https://democracy.cheltenham.gov.uk/documents/s53359/Appendix%209%20-%20Council%20270226%20Council%20Tax%20Support%20Scheme%20for%20Working%20Age%20Customers%202026-27%20Final.pdf"

    def formula(benunit, period, parameters):
        uc_award_before_deductions = max_(
            benunit("universal_credit_pre_benefit_cap", period),
            benunit("universal_credit", period),
        )
        has_uc_award = uc_award_before_deductions > 0
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
        childcare_deduction = benunit(
            "cheltenham_council_tax_reduction_childcare_deduction", period
        )
        non_uc_net_earnings_before_childcare = max_(
            0, gross_earnings - earnings_deductions
        )
        childcare_not_used_against_earnings = max_(
            0, childcare_deduction - non_uc_net_earnings_before_childcare
        )
        non_uc_net_earnings = max_(
            0, non_uc_net_earnings_before_childcare - childcare_deduction
        )
        uc_earnings = benunit(
            "cheltenham_council_tax_reduction_uc_earned_income_before_disregard",
            period,
        )
        net_earnings = where(has_uc_award, uc_earnings, non_uc_net_earnings)
        has_earnings = where(has_uc_award, uc_earnings > 0, gross_earnings > 0)
        earnings_disregard = (
            has_earnings
            * benunit("cheltenham_council_tax_reduction_earnings_disregard", period)
            * WEEKS_IN_YEAR
        )
        countable_earnings = max_(0, net_earnings - earnings_disregard)
        other_income = benunit.sum(
            claimant_or_partner
            * add(
                person,
                period,
                [
                    "property_income",
                    "private_pension_income",
                    "maintenance_income",
                    "savings_interest_income",
                    "dividend_income",
                    "state_pension",
                    "miscellaneous_income",
                ],
            )
        )
        tax_credits = benunit("tax_credits", period)
        tax_credits_after_childcare = where(
            tax_credits > 0,
            max_(0, tax_credits - childcare_not_used_against_earnings),
            tax_credits,
        )
        benefit_income = tax_credits_after_childcare + add(
            benunit,
            period,
            [
                "child_benefit",
                "carers_allowance",
                "attendance_allowance",
                "dla",
                "pip",
                "armed_forces_independence_payment",
                "housing_benefit",
                "jsa_contrib",
                "esa_contrib",
            ],
        )
        non_uc_disregarded_income = add(
            benunit,
            period,
            [
                "child_benefit",
                "attendance_allowance",
                "dla",
                "pip",
                "armed_forces_independence_payment",
                "housing_benefit",
                "cheltenham_council_tax_reduction_source_disregarded_income",
            ],
        ) + benunit.sum(claimant_or_partner * person("maintenance_income", period))
        non_uc_income = countable_earnings + max_(
            0,
            other_income + benefit_income - non_uc_disregarded_income,
        )
        countable_uc_award = max_(
            0,
            uc_award_before_deductions
            - add(
                benunit,
                period,
                [
                    "uc_housing_costs_element",
                    "uc_carer_element",
                    "uc_LCWRA_element",
                    "cheltenham_council_tax_reduction_uc_transitional_protection",
                ],
            ),
        )
        uc_disregarded_unearned_income = benunit.sum(
            claimant_or_partner
            * add(
                person,
                period,
                [
                    "attendance_allowance",
                    "dla",
                    "pip",
                    "armed_forces_independence_payment",
                    "maintenance_income",
                ],
            )
        ) + add(
            benunit,
            period,
            [
                "child_benefit",
                "housing_benefit",
                "cheltenham_council_tax_reduction_source_disregarded_income",
            ],
        )
        uc_income = (
            countable_earnings
            + max_(
                0,
                benunit("uc_unearned_income", period) - uc_disregarded_unearned_income,
            )
            + countable_uc_award
        )
        disabled_child_disregard = benunit(
            "cheltenham_council_tax_reduction_disabled_child_disregard", period
        )
        annual_income = max_(
            0, where(has_uc_award, uc_income, non_uc_income) - disabled_child_disregard
        )
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        weekly_income = where(relevant_income_based_benefit, 0, annual_income) / (
            WEEKS_IN_YEAR
        )
        return np.round(weekly_income * 100) / 100
