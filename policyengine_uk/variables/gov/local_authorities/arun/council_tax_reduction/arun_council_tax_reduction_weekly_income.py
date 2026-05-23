from policyengine_uk.model_api import *


class arun_council_tax_reduction_weekly_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Arun Council Tax Reduction weekly net income"
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.arun.gov.uk/download.cfm?doc=docm93jijm4n20657.pdf&ver=27819"
    )

    def formula(benunit, period, parameters):
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
        childcare_deduction = benunit(
            "arun_council_tax_reduction_childcare_deduction", period
        )
        non_uc_net_earnings = max_(
            0, gross_earnings - earnings_deductions - childcare_deduction
        )
        earnings_disregard = benunit(
            "arun_council_tax_reduction_earnings_disregard", period
        )
        countable_non_uc_earnings = max_(0, non_uc_net_earnings - earnings_disregard)
        uc_earned_income = benunit("uc_earned_income", period)
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
                "housing_benefit",
                "jsa_contrib",
                "esa_contrib",
            ],
        )
        disregarded_income = add(
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
                "arun_council_tax_reduction_source_disregarded_income",
            ],
        ) + benunit.sum(claimant_or_partner * person("maintenance_income", period))
        non_uc_income = countable_non_uc_earnings + max_(
            0,
            other_income + benefit_income - disregarded_income,
        )
        uc_award = benunit("universal_credit", period)
        countable_uc_award = max_(
            0,
            uc_award
            - add(
                benunit,
                period,
                [
                    "uc_housing_costs_element",
                    "uc_carer_element",
                    "uc_LCWRA_element",
                    "arun_council_tax_reduction_source_uc_disregarded_elements",
                ],
            ),
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
                "child_benefit",
                "housing_benefit",
                "arun_council_tax_reduction_source_disregarded_income",
            ],
        )
        uc_income = uc_earned_income + max_(
            0,
            benunit("uc_unearned_income", period)
            + countable_uc_award
            - uc_disregarded_unearned_income,
        )
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        annual_income = where(has_uc_award, uc_income, non_uc_income)
        weekly_income = where(relevant_income_based_benefit, 0, annual_income) / (
            WEEKS_IN_YEAR
        )
        return np.round(max_(0, weekly_income) * 100) / 100
