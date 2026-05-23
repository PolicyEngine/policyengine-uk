from policyengine_uk.model_api import *


class buckinghamshire_council_tax_reduction_weekly_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Buckinghamshire Council Tax Reduction weekly net income"
    definition_period = YEAR
    unit = GBP
    reference = "https://buckinghamshire.moderngov.co.uk/documents/s115727/Appendix%204%20Council%20Tax%20Reduction%20Scheme%20Policy.pdf"

    def formula(benunit, period, parameters):
        ctr = parameters(
            period
        ).gov.local_authorities.buckinghamshire.council_tax_reduction
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
        uc_net_earnings = benunit("uc_earned_income", period)
        net_earnings = where(has_uc_award, uc_net_earnings, non_uc_net_earnings)
        has_earnings = where(has_uc_award, uc_net_earnings > 0, gross_earnings > 0)
        countable_earnings = max_(
            0,
            net_earnings - has_earnings * ctr.income_disregard.earnings * WEEKS_IN_YEAR,
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
                "carers_allowance",
                "attendance_allowance",
                "dla",
                "pip",
                "armed_forces_independence_payment",
                "housing_benefit",
                "buckinghamshire_council_tax_reduction_esa_support_component",
                "buckinghamshire_council_tax_reduction_source_disregarded_income",
            ],
        )
        non_uc_non_earnings = max_(
            0, other_income + benefit_income - non_uc_disregarded_income
        )
        countable_uc = benunit(
            "buckinghamshire_council_tax_reduction_countable_universal_credit",
            period,
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
            [
                "housing_benefit",
                "buckinghamshire_council_tax_reduction_esa_support_component",
                "buckinghamshire_council_tax_reduction_source_disregarded_income",
            ],
        )
        uc_income = (
            countable_earnings
            + max_(
                0,
                benunit("uc_unearned_income", period) - uc_disregarded_unearned_income,
            )
            + countable_uc
        )
        non_uc_income = max_(
            0,
            countable_earnings + non_uc_non_earnings,
        )
        annual_income = where(has_uc_award, uc_income, non_uc_income)
        disabled = benunit(
            "buckinghamshire_council_tax_reduction_disability_income_disregard",
            period,
        )
        weekly_income = max_(
            0,
            annual_income / WEEKS_IN_YEAR - disabled * ctr.income_disregard.disability,
        )
        passported = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        return np.round(where(passported, 0, weekly_income) * 100) / 100
