from policyengine_uk.model_api import *


class north_yorkshire_council_tax_reduction_weekly_income(Variable):
    value_type = float
    entity = BenUnit
    label = "North Yorkshire Council Tax Reduction weekly income"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.northyorks.gov.uk/sites/default/files/2026-03/North%20Yorkshire%20Council%27s%20Council%20Tax%20Reduction%20Scheme%202026%20to%202027.pdf"

    def formula(benunit, period, parameters):
        ctr = parameters(
            period
        ).gov.local_authorities.north_yorkshire.council_tax_reduction
        has_uc_award = benunit("universal_credit", period) > 0
        uc_weekly_income = benunit(
            "north_yorkshire_council_tax_reduction_uc_weekly_income", period
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
        weekly_net_earnings = (
            max_(0, gross_earnings - earnings_deductions) / WEEKS_IN_YEAR
        )
        earnings_disregard = select(
            [
                benunit("is_single_person", period),
                benunit("is_couple", period) | benunit("is_lone_parent", period),
            ],
            [
                ctr.earnings_disregard.single,
                ctr.earnings_disregard.couple_or_lone_parent,
            ],
            default=0,
        )
        countable_weekly_earnings = max_(
            0, weekly_net_earnings - (gross_earnings > 0) * earnings_disregard
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
                "jsa_contrib",
                "esa_contrib",
                "working_tax_credit",
                "child_tax_credit",
            ],
        )
        non_uc_weekly_income = (
            countable_weekly_earnings
            + max_(0, other_income + benefit_income) / WEEKS_IN_YEAR
        )
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        weekly_income = where(
            relevant_income_based_benefit,
            0,
            where(has_uc_award, uc_weekly_income, non_uc_weekly_income),
        )
        return np.round(weekly_income * 100) / 100
