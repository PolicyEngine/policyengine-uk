from policyengine_uk.model_api import *


class plymouth_council_tax_reduction_weekly_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Plymouth Council Tax Support weekly income"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.plymouth.gov.uk/sites/default/files/2026-03/Plymouth-CTR-Scheme-2026-2027.pdf"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.plymouth.council_tax_reduction
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
            )
        )
        earnings_deductions = benunit.sum(
            claimant_or_partner
            * (
                person("income_tax", period)
                + person("national_insurance", period)
                + person("pension_contributions", period)
            )
        )
        childcare_deduction = benunit(
            "plymouth_council_tax_reduction_childcare_deduction", period
        )
        non_uc_net_earnings = max_(
            0, gross_earnings - earnings_deductions - childcare_deduction
        )
        uc_net_earnings = benunit("uc_earned_income", period)
        net_earnings = where(has_uc_award, uc_net_earnings, non_uc_net_earnings)
        has_earnings = where(has_uc_award, uc_net_earnings > 0, gross_earnings > 0)
        earnings_disregard = (
            has_earnings
            * benunit("plymouth_council_tax_reduction_earnings_disregard", period)
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
        benefit_income = add(
            benunit,
            period,
            [
                "tax_credits",
                "child_benefit",
                "carers_allowance",
                "attendance_allowance",
                "dla",
                "pip",
                "armed_forces_independence_payment",
                "jsa_contrib",
                "esa_contrib",
            ],
        )
        esa_component = min_(
            benunit("plymouth_council_tax_reduction_esa_support_component", period),
            benunit.sum(claimant_or_partner * person("esa_contrib", period)),
        )
        non_uc_disregarded_income = (
            add(
                benunit,
                period,
                [
                    "child_benefit",
                    "carers_allowance",
                    "attendance_allowance",
                    "dla",
                    "pip",
                    "armed_forces_independence_payment",
                    "plymouth_council_tax_reduction_source_disregarded_income",
                ],
            )
            + benunit.sum(claimant_or_partner * person("maintenance_income", period))
            + esa_component
        )
        non_uc_income = countable_earnings + max_(
            0, other_income + benefit_income - non_uc_disregarded_income
        )
        countable_uc_award = max_(
            0,
            uc_award_before_deductions - benunit("uc_housing_costs_element", period),
        )
        uc_disregarded_unearned_income = benunit.sum(
            claimant_or_partner
            * add(
                person,
                period,
                [
                    "carers_allowance",
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
                "plymouth_council_tax_reduction_source_disregarded_income",
                "plymouth_council_tax_reduction_esa_support_component",
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
        annual_income_before_disability_disregard = where(
            has_uc_award,
            uc_income,
            non_uc_income,
        )
        disability_income_disregard = benunit(
            "plymouth_council_tax_reduction_disability_income_disregard", period
        )
        annual_income = max_(
            0,
            annual_income_before_disability_disregard - disability_income_disregard,
        )
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        weekly_income = where(relevant_income_based_benefit, 0, annual_income) / (
            WEEKS_IN_YEAR
        )
        return np.round(weekly_income * 100) / 100
