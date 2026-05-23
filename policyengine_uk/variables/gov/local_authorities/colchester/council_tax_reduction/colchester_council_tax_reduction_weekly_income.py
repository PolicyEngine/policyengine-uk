from policyengine_uk.model_api import *


class colchester_council_tax_reduction_weekly_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Colchester Council Tax Reduction weekly income"
    definition_period = YEAR
    unit = GBP
    reference = "https://cbccrmdata.blob.core.windows.net/noteattachment/CBC-null-Local-council-tax-support-policy-updated-01-04-26-Local%20Council%20Tax%20support%20policy.pdf"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.colchester.council_tax_reduction
        uc_award_before_deductions = max_(
            benunit("universal_credit_pre_benefit_cap", period),
            benunit("universal_credit", period),
        )
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
            "colchester_council_tax_reduction_childcare_deduction", period
        )
        non_uc_net_earnings = max_(
            0, gross_earnings - earnings_deductions - childcare_deduction
        )
        net_earnings = where(
            has_uc_award, benunit("uc_earned_income", period), non_uc_net_earnings
        )
        has_earnings = where(has_uc_award, net_earnings > 0, gross_earnings > 0)
        earnings_disregard = where(
            has_uc_award,
            0,
            has_earnings * ctr.earnings_disregard.amount * WEEKS_IN_YEAR,
        )
        countable_earnings = max_(
            0,
            net_earnings - earnings_disregard,
        )
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
        non_uc_disregarded_income = add(
            benunit,
            period,
            [
                "child_benefit",
                "carers_allowance",
                "attendance_allowance",
                "dla",
                "pip",
                "armed_forces_independence_payment",
                "colchester_council_tax_reduction_source_disregarded_income",
            ],
        )
        non_uc_income = countable_earnings + max_(
            0, other_income + benefit_income - non_uc_disregarded_income
        )
        countable_uc_award = max_(
            0,
            uc_award_before_deductions
            - add(
                benunit,
                period,
                [
                    "uc_housing_costs_element",
                    "uc_disability_elements",
                    "uc_carer_element",
                    "uc_childcare_element",
                    "colchester_council_tax_reduction_source_disregarded_uc_elements",
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
                ],
            )
        ) + add(
            benunit,
            period,
            ["colchester_council_tax_reduction_source_disregarded_income"],
        )
        uc_income = (
            countable_earnings
            + max_(
                0,
                benunit("uc_unearned_income", period) - uc_disregarded_unearned_income,
            )
            + countable_uc_award
        )
        annual_income = where(has_uc_award, uc_income, non_uc_income)
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        weekly_income = where(relevant_income_based_benefit, 0, annual_income) / (
            WEEKS_IN_YEAR
        )
        return np.round(weekly_income * 100) / 100
