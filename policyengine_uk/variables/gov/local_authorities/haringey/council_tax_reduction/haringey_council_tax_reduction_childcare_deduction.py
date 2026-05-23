from policyengine_uk.model_api import *


class haringey_council_tax_reduction_childcare_deduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Haringey CTR childcare deduction from earnings"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.haringey.council_tax_reduction
        childcare = ctr.childcare
        person = benunit.members
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        claimant_or_partner = person("is_adult", period) & ~child_or_young_person
        works_enough_hours = person("weekly_hours", period) >= childcare.work_hours
        lone_parent_working = benunit("is_lone_parent", period) & benunit.any(
            claimant_or_partner & works_enough_hours
        )
        couple_both_working = benunit("is_couple", period) & benunit.all(
            works_enough_hours | ~claimant_or_partner
        )
        unable_to_work = (
            (person("pip_dl", period) > 0)
            | (person("dla_sc", period) > 0)
            | (person("attendance_allowance", period) > 0)
            | (person("armed_forces_independence_payment", period) > 0)
            | (person("incapacity_benefit", period) > 0)
            | person("uc_limited_capability_for_WRA", period)
        ) & claimant_or_partner
        couple_one_working_one_disabled = (
            benunit("is_couple", period)
            & benunit.any(claimant_or_partner & works_enough_hours)
            & benunit.any(unable_to_work)
        )
        eligible_work = (
            lone_parent_working | couple_both_working | couple_one_working_one_disabled
        )
        eligible_child = person("is_child", period) & (
            (person("age", period) < 15)
            | (
                (person("age", period) < 16)
                & person("is_disabled_for_benefits", period)
            )
        )
        eligible_children = benunit.sum(eligible_child)
        weekly_maximum = select(
            [
                eligible_children >= 2,
                eligible_children == 1,
            ],
            [
                childcare.weekly_maximum.two_or_more_children,
                childcare.weekly_maximum.one_child,
            ],
            default=0,
        )
        childcare_expenses = add(benunit, period, ["childcare_expenses"])
        return eligible_work * min_(childcare_expenses, weekly_maximum * WEEKS_IN_YEAR)
