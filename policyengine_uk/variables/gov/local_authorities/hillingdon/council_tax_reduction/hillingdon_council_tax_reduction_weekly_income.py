from policyengine_uk.model_api import *


class hillingdon_council_tax_reduction_weekly_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Hillingdon CTR weekly net income"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.hillingdon.council_tax_reduction
        person = benunit.members
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        claimant_or_partner = person("is_adult", period) & ~child_or_young_person
        earned_income = benunit.sum(
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
        has_uc = benunit("universal_credit", period) > 0
        earnings_disregard = where(
            (earned_income > 0) & ~has_uc,
            ctr.earnings_disregard.amount * WEEKS_IN_YEAR,
            0,
        )
        net_earnings = max_(0, earned_income - earnings_deductions - earnings_disregard)
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
        countable_uc = benunit(
            "hillingdon_council_tax_reduction_countable_universal_credit",
            period,
        )
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit",
            period,
        )
        uc_no_other_income = has_uc & (earned_income <= 0) & (other_income <= 0)
        income = where(
            relevant_income_based_benefit | uc_no_other_income,
            0,
            net_earnings + other_income + countable_uc,
        )
        return income / WEEKS_IN_YEAR
