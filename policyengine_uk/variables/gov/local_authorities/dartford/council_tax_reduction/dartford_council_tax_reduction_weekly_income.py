from policyengine_uk.model_api import *


class dartford_council_tax_reduction_weekly_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Dartford Council Tax Reduction weekly net income"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.dartford.gov.uk/downloads/file/2814/local-council-tax-reduction-scheme-dbc-2026-2027"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.dartford.council_tax_reduction
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
        net_earnings = max_(0, gross_earnings - earnings_deductions)
        earnings_disregard = (
            (gross_earnings > 0)
            * ~has_uc_award
            * ctr.earnings_disregard.amount
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
                "dartford_council_tax_reduction_source_disregarded_income",
            ],
        ) + benunit.sum(claimant_or_partner * person("maintenance_income", period))
        non_uc_income = countable_earnings + max_(
            0, other_income + benefit_income - disregarded_income
        )
        uc_disregarded_unearned_income = add(
            benunit,
            period,
            [
                "carers_allowance",
                "dartford_council_tax_reduction_source_disregarded_income",
            ],
        )
        uc_income = (
            benunit("uc_earned_income", period)
            + max_(
                0,
                benunit("uc_unearned_income", period) - uc_disregarded_unearned_income,
            )
            + max_(
                0,
                benunit("universal_credit", period)
                - benunit("uc_housing_costs_element", period),
            )
        )
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        annual_income = where(has_uc_award, uc_income, non_uc_income)
        weekly_income = where(relevant_income_based_benefit, 0, annual_income) / (
            WEEKS_IN_YEAR
        )
        return np.round(max_(0, weekly_income) * 100) / 100
