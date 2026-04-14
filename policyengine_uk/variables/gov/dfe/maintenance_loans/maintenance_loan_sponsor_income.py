from policyengine_uk.model_api import *


class maintenance_loan_sponsor_income(Variable):
    value_type = float
    entity = Person
    label = "Maintenance loan sponsor income"
    documentation = (
        "Proxy sponsor income used for maintenance loan assessment. "
        "This captures the selected sponsor benefit unit's income."
    )
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        household = person.household
        age = person("age", period)
        in_higher_education = person("maintenance_loan_in_higher_education", period)
        adult_index = person("adult_index", period)
        is_adult = person("is_adult", period)
        in_he = in_higher_education | person("in_HE", period)
        benunit_income = person("maintenance_loan_candidate_benunit_income", period)

        sponsor_candidate = is_adult & np.logical_not(in_he) & (age >= 29)
        head_candidate = sponsor_candidate & (adult_index == 1)
        second_candidate = sponsor_candidate & (adult_index == 2)

        head_age = household.max(head_candidate * age)
        second_age = household.max(second_candidate * age)
        head_income = household.sum(head_candidate * benunit_income)
        second_income = household.sum(second_candidate * benunit_income)

        head_eligible = (head_age >= age + 10) & (head_age <= age + 35)
        second_eligible = (second_age >= age + 10) & (second_age <= age + 35)

        sponsor_income = where(second_eligible, second_income, head_income)
        has_sponsor = in_higher_education & (head_eligible | second_eligible)

        return where(has_sponsor, sponsor_income, 0)
