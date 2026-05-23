from policyengine_uk.model_api import *


class brentwood_council_tax_reduction_weekly_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Brentwood Council Tax Reduction assessed weekly income"
    documentation = "Weekly applicant-and-partner income used to look up the Schedule 1 discount band. UC claimants use the DWP-assessed UC income calculation (paragraph 12) - the gross UC award (before deductions for loans, sanctions, advances or third-party payments) plus DWP-assessed earnings and other income, with a 20 pound weekly earnings disregard. Non-UC applicants use net earnings after tax, NI, half pension contributions, the 20 pound weekly earnings disregard, plus countable income other than earnings."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.brentwood.gov.uk/sites/default/files/2026-03/Council%20Tax%20reduction%20scheme%20S13A%202026-27%20FINAL.pdf"

    def formula(benunit, period, parameters):
        person = benunit.members
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        claimant_or_partner = person("is_adult", period) & ~child_or_young_person
        has_uc_award = (
            max_(
                benunit("universal_credit_pre_benefit_cap", period),
                benunit("universal_credit", period),
            )
            > 0
        )
        # UC paragraph 12.5: gross UC award before deductions; paragraph 12.7: x 12 / 52.
        # Paragraph 12.6(d): GBP 20 weekly earnings disregard.
        uc_earned_income = benunit("uc_earned_income", period)
        uc_earnings_disregard = (uc_earned_income > 0) * 20 * WEEKS_IN_YEAR
        uc_income = (
            max_(0, uc_earned_income - uc_earnings_disregard)
            + benunit("uc_unearned_income", period)
            + benunit("universal_credit_pre_benefit_cap", period)
        )
        # Non-UC: net earnings after tax/NI/half-pension contributions, then
        # paragraph 23.2/25.2's GBP 20 weekly earnings disregard.
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
        earnings_disregard = (gross_earnings > 0) * 20 * WEEKS_IN_YEAR
        countable_earnings = max_(0, net_earnings - earnings_disregard)
        other_income = benunit.sum(
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
                    "miscellaneous_income",
                ],
            )
        )
        benefit_income = add(
            benunit,
            period,
            [
                "tax_credits",
                "carers_allowance",
                "jsa_contrib",
                "esa_contrib",
            ],
        )
        non_uc_income = countable_earnings + other_income + benefit_income
        annual_income = where(has_uc_award, uc_income, non_uc_income)
        return annual_income / WEEKS_IN_YEAR
