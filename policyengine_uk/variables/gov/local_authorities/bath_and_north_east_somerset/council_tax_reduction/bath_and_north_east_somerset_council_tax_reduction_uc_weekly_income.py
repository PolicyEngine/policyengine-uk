from policyengine_uk.model_api import *


class bath_and_north_east_somerset_council_tax_reduction_uc_weekly_income(Variable):
    value_type = float
    entity = BenUnit
    label = (
        "Bath and North East Somerset Council Tax Reduction UC Class F weekly income"
    )
    definition_period = YEAR
    unit = GBP
    reference = "https://www.bathnes.gov.uk/sites/default/files/2026-01/Council_Tax_reduction_scheme_April_1_2026_to_March_31_2027.pdf"

    def formula(benunit, period, parameters):
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
        earnings_deductions = benunit.sum(
            claimant_or_partner
            * (
                person("income_tax", period)
                + person("national_insurance", period)
                + person("pension_contributions", period)
            )
        )
        uc_net_earnings = max_(
            0,
            benunit.sum(
                claimant_or_partner * person("uc_mif_capped_earned_income", period)
            )
            - earnings_deductions,
        )
        uc_award_before_deductions = max_(
            benunit("universal_credit_pre_benefit_cap", period),
            benunit("universal_credit", period),
        )
        counted_uc_award = max_(
            0,
            uc_award_before_deductions
            - benunit("uc_housing_costs_element", period)
            - benunit("uc_childcare_element", period),
        )
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
        disregarded_income = add(
            benunit,
            period,
            [
                "attendance_allowance",
                "dla",
                "pip",
            ],
        )
        uc_income = (
            uc_net_earnings
            + counted_uc_award
            + max_(
                0,
                benunit("uc_unearned_income", period)
                + other_income
                - disregarded_income,
            )
        )
        weekly_income = where(has_uc_award, uc_income / WEEKS_IN_YEAR, 0)
        return np.round(weekly_income * 100) / 100
