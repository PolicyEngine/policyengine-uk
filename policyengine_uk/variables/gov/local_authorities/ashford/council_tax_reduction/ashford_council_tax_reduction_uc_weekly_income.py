from policyengine_uk.model_api import *


class ashford_council_tax_reduction_uc_weekly_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Ashford Council Tax Reduction weekly Universal Credit income"
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.ashford.gov.uk/media/0n4nud13/ashford-ctr-scheme-2026-final.pdf"
    )

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.ashford.council_tax_reduction
        has_uc_award = benunit("universal_credit", period) > 0
        earnings_disregard = benunit(
            "ashford_council_tax_reduction_earnings_disregard", period
        )
        uc_earned_income = max_(
            0, benunit("uc_earned_income", period) - earnings_disregard
        )
        uc_award = benunit("universal_credit", period)
        disregarded_uc_elements = add(
            benunit,
            period,
            [
                "uc_housing_costs_element",
                "uc_child_element",
                "uc_carer_element",
                "uc_childcare_element",
                "uc_disability_elements",
                "ashford_council_tax_reduction_source_uc_disregarded_elements",
            ],
        )
        countable_uc_award = max_(0, uc_award - disregarded_uc_elements)
        person = benunit.members
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        claimant_or_partner = person("is_adult", period) & ~child_or_young_person
        uc_unearned_income_disregards = benunit.sum(
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
                "child_benefit",
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
        uc_other_income = max_(
            0,
            benunit("uc_unearned_income", period)
            + countable_uc_award
            - uc_unearned_income_disregards
            - disability_or_carer_disregard,
        )
        return has_uc_award * (uc_earned_income + uc_other_income) / WEEKS_IN_YEAR
