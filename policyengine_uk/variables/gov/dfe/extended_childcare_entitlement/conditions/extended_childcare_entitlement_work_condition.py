from policyengine_uk.model_api import *


class extended_childcare_entitlement_work_condition(Variable):
    value_type = bool
    entity = Person
    label = "Work conditions for extended childcare entitlement"
    documentation = "Whether this person meets work requirements for extended childcare entitlement."
    definition_period = YEAR
    defined_for = "is_parent"

    def formula(person, period, parameters):
        benunit = person.benunit
        in_work = person("in_work", period)

        p = parameters(period).gov.dfe.extended_childcare_entitlement
        disability_criteria = list(p.disability_criteria)
        person_disability_criteria = [
            variable
            for variable in disability_criteria
            if person.entity.get_variable(variable).entity.is_person
        ]
        group_disability_criteria = [
            variable
            for variable in disability_criteria
            if not person.entity.get_variable(variable).entity.is_person
        ]

        eligible_based_on_person_disability = (
            add(person, period, person_disability_criteria) > 0
            if person_disability_criteria
            else False
        )
        eligible_based_on_group_disability = (
            add(benunit, period, group_disability_criteria) > 0
            if group_disability_criteria
            else False
        )
        eligible_based_on_disability = (
            eligible_based_on_person_disability | eligible_based_on_group_disability
        )

        # Count parents in benefit unit
        parent_count = benunit.sum(person("is_parent", period))

        # Eligibility conditions for lone parents
        lone_parent_eligible = (parent_count == 1) & in_work

        # Break out the complex nested conditions for couples
        all_parents_working = benunit.all(in_work | ~person("is_parent", period))
        some_parents_working = benunit.any(in_work & person("is_parent", period))
        any_parent_disability_eligible = benunit.any(
            eligible_based_on_disability & person("is_parent", period)
        )

        # Work condition for couples - either both working or one working with other disabled or receiving UC Carer Element
        couple_work_condition = all_parents_working | (
            some_parents_working & any_parent_disability_eligible
        )

        couple_eligible = (parent_count == 2) & couple_work_condition

        return lone_parent_eligible | couple_eligible
