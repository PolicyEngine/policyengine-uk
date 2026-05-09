from policyengine_uk.model_api import *


class cheltenham_council_tax_reduction_support_rate(Variable):
    value_type = float
    entity = BenUnit
    label = "Cheltenham Council Tax Support rate"
    definition_period = YEAR
    reference = "https://democracy.cheltenham.gov.uk/documents/s53359/Appendix%209%20-%20Council%20270226%20Council%20Tax%20Support%20Scheme%20for%20Working%20Age%20Customers%202026-27%20Final.pdf"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.cheltenham.council_tax_reduction
        weekly_income = benunit(
            "cheltenham_council_tax_reduction_weekly_income", period
        )
        weekly_income_for_band = weekly_income + 1e-9
        person = benunit.members
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        num_children = benunit.sum(child_or_young_person)
        is_couple = benunit("is_couple", period)
        is_lone_parent = benunit("is_lone_parent", period)
        bands = ctr.income_band
        banded_support_rate = select(
            [
                is_couple & (num_children >= 4),
                is_couple & (num_children == 3),
                is_couple & (num_children > 0),
                is_lone_parent & (num_children >= 4),
                is_lone_parent & (num_children == 3),
                is_lone_parent & (num_children > 0),
                is_couple,
            ],
            [
                bands.couple_four_or_more_children.calc(weekly_income_for_band),
                bands.couple_three_children.calc(weekly_income_for_band),
                bands.couple_up_to_two_children.calc(weekly_income_for_band),
                bands.lone_parent_four_or_more_children.calc(weekly_income_for_band),
                bands.lone_parent_three_children.calc(weekly_income_for_band),
                bands.lone_parent_up_to_two_children.calc(weekly_income_for_band),
                bands.couple.calc(weekly_income_for_band),
            ],
            default=bands.single.calc(weekly_income_for_band),
        )
        uc_award_before_deductions = max_(
            benunit("universal_credit_pre_benefit_cap", period),
            benunit("universal_credit", period),
        )
        uc_non_earner = (uc_award_before_deductions > 0) & (
            benunit(
                "cheltenham_council_tax_reduction_uc_earned_income_before_disregard",
                period,
            )
            <= 0
        )
        passported_band_1 = (
            (benunit("income_support", period) > 0)
            | (benunit("jsa_income", period) > 0)
            | (benunit("esa_income", period) > 0)
            | uc_non_earner
        )
        return where(passported_band_1, 1, banded_support_rate)
