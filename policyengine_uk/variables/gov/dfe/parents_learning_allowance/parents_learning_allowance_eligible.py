from policyengine_uk.model_api import *


class parents_learning_allowance_eligible(Variable):
    value_type = bool
    entity = Person
    label = "Eligible for Parents' Learning Allowance"
    documentation = (
        "Whether the person is eligible for Parents' Learning Allowance under the England student-finance scheme. "
        "This is a first-pass model using the published household-income cutoff and an explicit course-eligibility "
        "override, with the maintenance-loan pathway as the default proxy."
    )
    definition_period = YEAR
    defined_for = "would_claim_parents_learning_allowance"

    def formula(person, period, parameters):
        p = parameters(period).gov.dfe.parents_learning_allowance
        country = person.household("country", period)
        in_england = country == country.possible_values.ENGLAND
        is_parent = person("is_parent", period)
        dependent_children = person.benunit(
            "parents_learning_allowance_dependent_children", period
        )
        course_eligible = person("parents_learning_allowance_course_eligible", period)
        household_income = person("parents_learning_allowance_household_income", period)

        return (
            in_england
            & is_parent
            & (dependent_children > 0)
            & course_eligible
            & (household_income < p.income_limit)
        )
