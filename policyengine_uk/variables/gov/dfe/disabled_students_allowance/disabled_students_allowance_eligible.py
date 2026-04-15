from policyengine_uk.model_api import *


class disabled_students_allowance_eligible(Variable):
    value_type = bool
    entity = Person
    label = "Eligible for Disabled Students' Allowance"
    documentation = (
        "Whether the person is eligible for Student Finance England Disabled "
        "Students' Allowance. This first-pass model uses the published England "
        "coverage rule, a higher-education default course proxy, a narrow "
        "qualifying-condition proxy with explicit override, and an explicit "
        "equivalent-support exclusion."
    )
    definition_period = YEAR
    defined_for = "would_claim_disabled_students_allowance"

    def formula(person, period, parameters):
        in_england = person("maintenance_loan_in_england_system", period)
        course_eligible = person("disabled_students_allowance_course_eligible", period)
        qualifying_condition = person(
            "disabled_students_allowance_has_qualifying_condition", period
        )
        receives_equivalent_support = person(
            "disabled_students_allowance_receives_equivalent_support", period
        )
        expenses = person("disabled_students_allowance_eligible_expenses", period)

        return (
            in_england
            & course_eligible
            & qualifying_condition
            & ~receives_equivalent_support
            & (expenses > 0)
        )
