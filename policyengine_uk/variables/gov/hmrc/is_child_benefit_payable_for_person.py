from policyengine_uk.model_api import *


class is_child_benefit_payable_for_person(Variable):
    value_type = bool
    entity = Person
    label = "Child Benefit is payable for this person"
    documentation = (
        "Whether the benefit unit's Child Benefit includes an amount for this "
        "person: they are its child or qualifying young person, and Child "
        "Benefit is not barred by remunerative work. Child Benefit is not "
        "payable for a qualifying young person 'by virtue of' the terminal "
        "date rule for any week they are in remunerative work (Child Benefit "
        "(General) Regulations 2006 reg. 7(3)). So a young person who "
        "qualifies only through the terminal date, and works 24 hours or "
        "more a week, stays a qualifying young person (and a Housing Benefit "
        "young person) but brings no Child Benefit. One who also meets "
        "another condition is paid through that one (reg. 2(2))."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/223/regulation/2",
        "https://www.legislation.gov.uk/uksi/2006/223/regulation/7",
    )

    def formula(person, period, parameters):
        another_condition = (
            (
                person(
                    "meets_qualifying_young_person_education_or_training_condition_for_child_benefit",
                    period,
                )
                & person(
                    "meets_qualifying_young_person_entry_condition_for_child_benefit",
                    period,
                )
            )
            | person("is_before_first_september_following_16th_birthday", period)
            | person(
                "meets_qualifying_young_person_extension_period_condition_for_child_benefit",
                period,
            )
        )
        only_through_terminal_date = (
            person("is_qualifying_young_person_for_child_benefit", period)
            & ~person("is_child_for_child_benefit", period)
            & ~another_condition
        )
        barred = only_through_terminal_date & person(
            "is_in_remunerative_work_for_child_benefit", period
        )
        return (
            person("is_child_or_qualifying_young_person_for_child_benefit", period)
            & ~barred
        )
