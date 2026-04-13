from policyengine_uk.model_api import *


class maintenance_loan_has_sponsor(Variable):
    value_type = bool
    entity = Person
    label = "Has maintenance loan sponsor"
    documentation = "Whether the model detects a plausible sponsor in the household for maintenance loan purposes."
    definition_period = YEAR

    def formula(person, period, parameters):
        household = person.household
        age = person("age", period)
        in_higher_education = person("maintenance_loan_in_higher_education", period)
        adult_index = person("adult_index", period)
        is_adult = person("is_adult", period)
        in_he = in_higher_education | person("in_HE", period)

        sponsor_candidate = is_adult & np.logical_not(in_he) & (age >= 29)
        head_candidate = sponsor_candidate & (adult_index == 1)
        second_candidate = sponsor_candidate & (adult_index == 2)

        head_age = household.max(head_candidate * age)
        second_age = household.max(second_candidate * age)

        head_eligible = (head_age >= age + 10) & (head_age <= age + 35)
        second_eligible = (second_age >= age + 10) & (second_age <= age + 35)

        return in_higher_education & (head_eligible | second_eligible)
