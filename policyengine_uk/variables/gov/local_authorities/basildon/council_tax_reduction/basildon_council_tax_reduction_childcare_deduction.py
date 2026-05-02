from policyengine_uk.model_api import *


class basildon_council_tax_reduction_childcare_deduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Basildon Council Tax Reduction childcare deduction from earnings"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.basildon.gov.uk/media/11563/Basildon-Council-Council-Tax-Reduction-Scheme-2026-27/pdf/Basildon_S13A_202627_Final.pdf?m=1771316212763"

    def formula(benunit, period, parameters):
        childcare = parameters(
            period
        ).gov.local_authorities.basildon.council_tax_reduction.childcare
        person = benunit.members
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        claimant_or_partner = person("is_adult", period) & ~child_or_young_person
        earned_income = person("employment_income", period) + person(
            "self_employment_income", period
        )
        engaged_in_work = (person("weekly_hours", period) > 0) | (earned_income > 0)
        lone_parent_working = benunit("is_lone_parent", period) & benunit.any(
            claimant_or_partner & engaged_in_work
        )
        couple_both_working = benunit("is_couple", period) & benunit.all(
            engaged_in_work | ~claimant_or_partner
        )
        unable_to_work = (
            (person("pip_dl", period) > 0)
            | (person("dla_sc", period) > 0)
            | (person("attendance_allowance", period) > 0)
            | (person("armed_forces_independence_payment", period) > 0)
            | person("uc_limited_capability_for_WRA", period)
            | person(
                "basildon_council_tax_reduction_childcare_disabled_partner", period
            )
        ) & claimant_or_partner
        couple_one_working_one_disabled = (
            benunit("is_couple", period)
            & benunit.any(claimant_or_partner & engaged_in_work)
            & benunit.any(unable_to_work)
        )
        eligible_work = (
            lone_parent_working | couple_both_working | couple_one_working_one_disabled
        )
        eligible_child = child_or_young_person & (
            (person("age", period) < 15)
            | (
                (person("age", period) < 16)
                & (
                    person("is_disabled_for_benefits", period)
                    | person(
                        "basildon_council_tax_reduction_childcare_disabled_child",
                        period,
                    )
                )
            )
        )
        eligible_children = benunit.sum(eligible_child)
        weekly_maximum = select(
            [eligible_children >= 2, eligible_children == 1],
            [
                childcare.weekly_maximum.two_or_more_children,
                childcare.weekly_maximum.one_child,
            ],
            default=0,
        )
        childcare_expenses = add(benunit, period, ["childcare_expenses"])
        return eligible_work * min_(childcare_expenses, weekly_maximum * WEEKS_IN_YEAR)
