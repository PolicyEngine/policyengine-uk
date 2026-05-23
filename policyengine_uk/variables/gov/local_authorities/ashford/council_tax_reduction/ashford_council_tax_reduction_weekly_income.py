from policyengine_uk.model_api import *


class ashford_council_tax_reduction_weekly_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Ashford Council Tax Reduction weekly income"
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.ashford.gov.uk/media/0n4nud13/ashford-ctr-scheme-2026-final.pdf"
    )

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.ashford.council_tax_reduction
        has_uc_award = benunit("universal_credit", period) > 0
        uc_weekly_income = benunit(
            "ashford_council_tax_reduction_uc_weekly_income", period
        )
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
            "ashford_council_tax_reduction_childcare_deduction", period
        )
        net_earnings_before_childcare = max_(0, gross_earnings - earnings_deductions)
        childcare_not_used_against_earnings = max_(
            0, childcare_deduction - net_earnings_before_childcare
        )
        net_earnings = max_(0, net_earnings_before_childcare - childcare_deduction)
        earnings_disregard = benunit(
            "ashford_council_tax_reduction_earnings_disregard", period
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
                "carers_allowance",
                "attendance_allowance",
                "child_benefit",
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
                "carers_allowance",
                "child_benefit",
                "attendance_allowance",
                "dla",
                "pip",
                "armed_forces_independence_payment",
                "housing_benefit",
                "ashford_council_tax_reduction_source_disregarded_income",
            ],
        )
        disability_or_carer_disregard = (
            benunit(
                "ashford_council_tax_reduction_disability_or_carer_income_disregard",
                period,
            )
            * ctr.income_disregard.disability_or_carer
            * WEEKS_IN_YEAR
        )
        annual_income = countable_earnings + max_(
            0,
            other_income
            + benefit_income
            - disregarded_income
            - disability_or_carer_disregard,
        )
        weekly_income = where(
            has_uc_award,
            uc_weekly_income,
            annual_income / WEEKS_IN_YEAR
            + benunit("ashford_council_tax_reduction_weekly_tariff_income", period),
        )
        return np.round(weekly_income * 100) / 100
