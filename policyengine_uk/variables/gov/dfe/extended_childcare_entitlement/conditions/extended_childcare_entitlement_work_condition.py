from policyengine_uk.model_api import *


class extended_childcare_entitlement_work_condition(Variable):
    value_type = bool
    entity = Person
    label = "Work conditions for extended childcare entitlement"
    documentation = "Whether the person/couple meets work requirements for extended childcare entitlement"
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

        # Count parents in benefit unit
        parent_count = add(benunit, period, ["is_parent"])

        # Eligibility conditions
        lone_parent_eligible = (parent_count == 1) & in_work

        # Break out the complex nested conditions
        all_parents_working = benunit.all(in_work | ~person("is_parent", period))
        some_parents_working = benunit.any(in_work & person("is_parent", period))
        some_parents_disability_eligible = benunit.any(
            eligible_based_on_disability & person("is_parent", period)
        )

        # Create a separate work condition
        couple_work_condition = all_parents_working | (
            some_parents_working & some_parents_disability_eligible
        )

        couple_eligible = (parent_count == 2) & couple_work_condition

        return lone_parent_eligible | couple_eligible