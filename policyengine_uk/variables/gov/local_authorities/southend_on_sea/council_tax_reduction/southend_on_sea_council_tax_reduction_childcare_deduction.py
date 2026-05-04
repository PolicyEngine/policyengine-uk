from policyengine_uk.model_api import *


class southend_on_sea_council_tax_reduction_childcare_deduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Southend-on-Sea Council Tax Reduction childcare deduction from earnings"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.southend.gov.uk/downloads/file/3527/southend-on-sea-borough-council-ctax-reduction-s13a-scheme"

    def formula(benunit, period, parameters):
        ctr = parameters(
            period
        ).gov.local_authorities.southend_on_sea.council_tax_reduction
        person = benunit.members
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        claimant_or_partner = person("is_adult", period) & ~child_or_young_person
        statutory_family_leave = add(
            person,
            period,
            [
                "statutory_sick_pay",
                "statutory_maternity_pay",
                "statutory_paternity_pay",
                "maternity_allowance",
            ],
        )
        in_remunerative_work = (
            (person("weekly_hours", period) >= ctr.childcare.work_hours)
            | (statutory_family_leave > 0)
        ) & claimant_or_partner
        lone_parent_working = benunit("is_lone_parent", period) & benunit.any(
            in_remunerative_work
        )
        couple_both_working = benunit("is_couple", period) & benunit.all(
            in_remunerative_work | ~claimant_or_partner
        )
        unable_to_work = (
            (person("pip_dl", period) > 0)
            | (person("dla_sc", period) > 0)
            | (person("attendance_allowance", period) > 0)
            | (person("armed_forces_independence_payment", period) > 0)
            | person("uc_limited_capability_for_WRA", period)
            | person(
                "southend_on_sea_council_tax_reduction_childcare_disabled_partner",
                period,
            )
        ) & claimant_or_partner
        couple_one_working_one_disabled = (
            benunit("is_couple", period)
            & benunit.any(in_remunerative_work)
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
                        "southend_on_sea_council_tax_reduction_childcare_disabled_child",
                        period,
                    )
                )
            )
        )
        eligible_children = benunit.sum(eligible_child)
        weekly_maximum = select(
            [eligible_children >= 2, eligible_children == 1],
            [
                ctr.childcare.weekly_maximum.two_or_more_children,
                ctr.childcare.weekly_maximum.one_child,
            ],
            default=0,
        )
        childcare_expenses = add(benunit, period, ["childcare_expenses"])
        return eligible_work * min_(childcare_expenses, weekly_maximum * WEEKS_IN_YEAR)
