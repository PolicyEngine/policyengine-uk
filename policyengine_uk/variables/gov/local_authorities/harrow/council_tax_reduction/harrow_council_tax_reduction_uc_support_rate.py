from policyengine_uk.model_api import *


class harrow_council_tax_reduction_uc_support_rate(Variable):
    value_type = float
    entity = BenUnit
    label = "Harrow Universal Credit CTS support rate"
    definition_period = YEAR
    reference = "https://www.harrow.gov.uk/downloads/file/33606/council-tax-support-scheme-2026-27"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.harrow.council_tax_reduction
        weekly_earnings = benunit(
            "harrow_council_tax_reduction_uc_weekly_earnings", period
        )
        person = benunit.members
        children = benunit.sum(
            person("is_child_or_qualifying_young_person_for_child_benefit", period)
        )
        is_couple = benunit("is_couple", period)
        is_lone_parent = benunit("is_lone_parent", period)
        single_without_children = ~is_couple & (children == 0)
        childless_couple = is_couple & (children == 0)
        lone_parent_up_to_two = is_lone_parent & (children <= 2)
        lone_parent_three_or_more = is_lone_parent & (children >= 3)
        couple_up_to_two = is_couple & (children > 0) & (children <= 2)
        couple_three_or_more = is_couple & (children >= 3)
        banded_rate = select(
            [
                single_without_children,
                childless_couple,
                lone_parent_up_to_two,
                lone_parent_three_or_more,
                couple_up_to_two,
                couple_three_or_more,
            ],
            [
                ctr.uc_earnings.single.calc(weekly_earnings),
                ctr.uc_earnings.childless_couple.calc(weekly_earnings),
                ctr.uc_earnings.lone_parent_up_to_two_children.calc(weekly_earnings),
                ctr.uc_earnings.lone_parent_three_or_more_children.calc(
                    weekly_earnings
                ),
                ctr.uc_earnings.couple_up_to_two_children.calc(weekly_earnings),
                ctr.uc_earnings.couple_three_or_more_children.calc(weekly_earnings),
            ],
            default=0.0,
        )
        maximum_uc = (benunit("universal_credit", period) > 0) & (
            benunit("universal_credit", period) >= benunit("uc_maximum_amount", period)
        )
        no_earned_income = weekly_earnings <= 0
        rate = where(
            maximum_uc | no_earned_income,
            ctr.maximum_support_rate.standard,
            banded_rate,
        )
        disabled = benunit("harrow_council_tax_reduction_disabled", period)
        return where(disabled, ctr.maximum_support_rate.disabled, rate)
