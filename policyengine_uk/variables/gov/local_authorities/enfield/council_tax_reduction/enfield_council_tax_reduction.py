from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_enfield_working_age,
)


class enfield_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Enfield Council Tax Reduction"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.enfield.council_tax_reduction
        local_authority = benunit.household("local_authority", period)
        country = benunit.household("country", period)
        has_pensioner = benunit.household(
            "council_tax_reduction_household_has_pensioner", period
        )
        working_age = is_enfield_working_age(local_authority, country, has_pensioner)
        protected = benunit("enfield_council_tax_reduction_protected_group", period)
        liability = benunit.household(
            "enfield_council_tax_reduction_maximum_eligible_liability", period
        )
        non_dep_deductions = benunit(
            "enfield_council_tax_reduction_non_dep_deductions", period
        )
        applicable_amount = benunit("council_tax_reduction_applicable_amount", period)
        applicable_income = benunit(
            "enfield_council_tax_reduction_applicable_income", period
        ) + benunit("enfield_council_tax_reduction_tariff_income", period)
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        excess_income = max_(0, applicable_income - applicable_amount)
        excess_income = where(relevant_income_based_benefit, 0, excess_income)
        non_uc_rate = where(
            protected,
            ctr.maximum_support_rate.protected,
            ctr.maximum_support_rate.non_protected,
        )
        non_uc_award = max_(
            0,
            liability * non_uc_rate
            - excess_income * ctr.means_test.withdrawal_rate
            - non_dep_deductions,
        )

        weekly_earnings = benunit(
            "enfield_council_tax_reduction_uc_weekly_earnings", period
        )
        person = benunit.members
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        num_children = benunit.sum(child_or_young_person)
        is_couple = benunit("is_couple", period)
        uc_bands = ctr.uc_income_band
        uc_rate = select(
            [
                protected & (num_children >= 2),
                protected & (num_children == 1),
                protected & is_couple,
                protected,
                num_children >= 2,
                num_children == 1,
                is_couple,
            ],
            [
                uc_bands.protected.family_two_or_more_children.calc(weekly_earnings),
                uc_bands.protected.family_one_child.calc(weekly_earnings),
                uc_bands.protected.couple.calc(weekly_earnings),
                uc_bands.protected.single.calc(weekly_earnings),
                uc_bands.non_protected.family_two_or_more_children.calc(
                    weekly_earnings
                ),
                uc_bands.non_protected.family_one_child.calc(weekly_earnings),
                uc_bands.non_protected.couple.calc(weekly_earnings),
            ],
            default=uc_bands.non_protected.single.calc(weekly_earnings),
        )
        uc_award = max_(0, liability * uc_rate - non_dep_deductions)
        has_uc_award = benunit("universal_credit", period) > 0
        award = where(has_uc_award, uc_award, non_uc_award)
        award = where(award < ctr.minimum_award * WEEKS_IN_YEAR, 0, award)
        non_uc_capital_eligible = (
            benunit.household("savings", period) <= ctr.means_test.capital_limit
        )
        uc_capital_eligible = (
            benunit("uc_assessable_capital", period) <= ctr.means_test.capital_limit
        )
        capital_eligible = where(
            has_uc_award, uc_capital_eligible, non_uc_capital_eligible
        )
        return (
            working_age
            * benunit("benunit_contains_household_head", period)
            * benunit("would_claim_council_tax_reduction", period)
            * capital_eligible
            * award
        )
