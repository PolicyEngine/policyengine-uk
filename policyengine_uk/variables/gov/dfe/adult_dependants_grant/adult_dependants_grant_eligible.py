from policyengine_uk.model_api import *


class adult_dependants_grant_eligible(Variable):
    value_type = bool
    entity = Person
    label = "Eligible for Adult Dependants' Grant"
    documentation = (
        "Whether the person is eligible for Adult Dependants' Grant under the England student-finance scheme. "
        "This first-pass model uses the published household-income and dependant-adult income tests, "
        "a higher-education default course proxy, and explicit inputs for hard-to-observe dependant-adult cases."
    )
    definition_period = YEAR
    defined_for = "would_claim_adult_dependants_grant"

    def formula(person, period, parameters):
        p = parameters(period).gov.dfe.adult_dependants_grant
        country = person.household("country", period)
        in_england = country == country.possible_values.ENGLAND

        course_eligible = person("adult_dependants_grant_course_eligible", period)
        adult_eligible = person("adult_dependants_grant_adult_eligible", period)
        adult_receives_student_finance = person(
            "adult_dependants_grant_adult_receives_student_finance", period
        )
        household_income = person("adult_dependants_grant_household_income", period)
        receives_postgraduate_loan = person(
            "adult_dependants_grant_receives_postgraduate_loan", period
        )

        return (
            in_england
            & course_eligible
            & adult_eligible
            & ~adult_receives_student_finance
            & ~receives_postgraduate_loan
            & (household_income < p.income_limit)
        )
