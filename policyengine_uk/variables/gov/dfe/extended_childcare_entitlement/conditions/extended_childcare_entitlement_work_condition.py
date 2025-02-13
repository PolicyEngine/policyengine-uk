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

        # Get disability status
        p = parameters(period).gov.dfe.extended_childcare_entitlement
        eligible_based_on_disability = (
            add(person, period, p.disability_criteria) > 0
        )

        # Adjust eligibility based on the summed UC Carer Element: 11A(1)(c)
        eligible_based_on_disability_or_carer = (
            eligible_based_on_disability
            | (benunit("uc_carer_element", period) > 0)
        )

        # Count parents in benefit unit
        parent_count = benunit.sum(person("is_parent", period))

        # Eligibility conditions for lone parents
        lone_parent_eligible = (parent_count == 1) & in_work

        # Break out the complex nested conditions for couples
        all_parents_working = benunit.all(
            in_work | ~person("is_parent", period)
        )
        some_parents_working = benunit.any(
            in_work & person("is_parent", period)
        )
        any_parent_disability_eligible = benunit.any(
            eligible_based_on_disability_or_carer & person("is_parent", period)
        )

        # Work condition for couples - either both working or one working with other disabled or receiving UC Carer Element
        couple_work_condition = all_parents_working | (
            some_parents_working & any_parent_disability_eligible
        )

        couple_eligible = (parent_count == 2) & couple_work_condition

        return lone_parent_eligible | couple_eligible
