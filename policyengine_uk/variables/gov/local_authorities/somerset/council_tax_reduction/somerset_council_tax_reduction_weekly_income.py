from policyengine_uk.model_api import *


class somerset_council_tax_reduction_weekly_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Somerset Council Tax Reduction weekly income"
    definition_period = YEAR
    unit = GBP
    reference = "https://somerset.moderngov.co.uk/documents/s59784/05a%20APPENDIX%203%20Somerset%20S13A%20202627%20Scheme%20DRAFT.pdf"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.somerset.council_tax_reduction
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
        non_uc_net_earnings = max_(0, gross_earnings - earnings_deductions)
        has_uc_award = benunit("universal_credit", period) > 0
        uc_net_earnings = benunit("uc_earned_income", period)
        net_earnings = where(has_uc_award, uc_net_earnings, non_uc_net_earnings)
        has_earnings = where(has_uc_award, uc_net_earnings > 0, gross_earnings > 0)
        earnings_disregard = (
            has_earnings * ctr.earnings_disregard.amount * WEEKS_IN_YEAR
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
                    "savings_interest_income",
                    "dividend_income",
                    "state_pension",
                    "miscellaneous_income",
                    "jsa_contrib",
                    "esa_contrib",
                ],
            )
        )
        tax_credits = add(
            benunit,
            period,
            [
                "working_tax_credit",
                "child_tax_credit",
            ],
        )
        esa_support_component = min_(
            benunit("somerset_council_tax_reduction_esa_support_component", period),
            benunit.sum(claimant_or_partner * person("esa_contrib", period)),
        )
        non_uc_income = countable_earnings + max_(
            0, other_income + tax_credits - esa_support_component
        )
        countable_uc_award = max_(
            0,
            benunit("universal_credit", period)
            - benunit("uc_housing_costs_element", period),
        )
        uc_disregarded_unearned_income = benunit.sum(
            claimant_or_partner * person("carers_allowance", period)
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
        disabled_income_disregard = benunit(
            "somerset_council_tax_reduction_disabled_income_disregard",
            period,
        )
        annual_income = max_(
            0,
            annual_income_before_disability_disregard
            - disabled_income_disregard
            * ctr.disabled_income_disregard.amount
            * WEEKS_IN_YEAR,
        )
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        weekly_income = where(relevant_income_based_benefit, 0, annual_income) / (
            WEEKS_IN_YEAR
        )
        return np.round(weekly_income * 100) / 100
