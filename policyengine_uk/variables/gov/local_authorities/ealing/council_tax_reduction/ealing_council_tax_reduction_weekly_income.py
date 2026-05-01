from policyengine_uk.model_api import *


class ealing_council_tax_reduction_weekly_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Ealing CTR weekly income"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.ealing.council_tax_reduction
        person = benunit.members
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        claimant_or_partner = person("is_adult", period) & ~child_or_young_person
        employment_income = benunit.sum(
            claimant_or_partner * person("employment_income", period)
        )
        self_employment_income = person("self_employment_income", period)
        self_employed = claimant_or_partner & (self_employment_income > 0)
        startup_period = person(
            "ealing_council_tax_reduction_self_employment_startup_period",
            period,
        )
        mif_applies = self_employed & ~startup_period
        national_living_wage = parameters(
            period
        ).gov.hmrc.minimum_wage.non_apprentice.calc(25)
        minimum_wage = mif_applies * national_living_wage
        weekly_mif = benunit.sum(minimum_wage) * 35
        weekly_mif = where(
            benunit("is_lone_parent", period),
            benunit.max(minimum_wage) * 16,
            weekly_mif,
        )
        weekly_mif = where(
            benunit("is_couple", period)
            & (benunit("num_children", period) > 0)
            & (benunit.sum(mif_applies) >= 2),
            benunit.max(minimum_wage) * 35
            + (benunit.sum(minimum_wage) - benunit.max(minimum_wage)) * 16,
            weekly_mif,
        )
        self_employment_income = benunit.sum(
            (self_employed & startup_period) * self_employment_income
        ) + max_(
            benunit.sum(mif_applies * self_employment_income),
            weekly_mif * WEEKS_IN_YEAR,
        )
        earned_income = employment_income + self_employment_income
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
            (earned_income > 0) & ~benunit("is_single_person", period) & ~has_uc,
            ctr.earnings_disregard.couple_or_lone_parent * WEEKS_IN_YEAR,
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
                    "maintenance_income",
                    "savings_interest_income",
                    "dividend_income",
                    "state_pension",
                    "miscellaneous_income",
                ],
            )
        )
        countable_uc = benunit(
            "ealing_council_tax_reduction_countable_universal_credit",
            period,
        )
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit",
            period,
        )
        income = where(
            relevant_income_based_benefit,
            0,
            where(has_uc, countable_uc, net_earnings + other_income),
        )
        return income / WEEKS_IN_YEAR
