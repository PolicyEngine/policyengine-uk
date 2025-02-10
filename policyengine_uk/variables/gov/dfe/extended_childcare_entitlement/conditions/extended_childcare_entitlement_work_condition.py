from policyengine_uk.model_api import *


class extended_childcare_entitlement_work_condition(Variable):
    value_type = bool
    entity = Person
    label = "Work conditions for extended childcare entitlement"
    documentation = "Whether the person/couple meets work requirements for extended childcare entitlement"
    definition_period = YEAR

    def formula(person, period, parameters):
        benunit = person.benunit
        is_child = person("is_child", period)
        in_work = person("in_work", period)
        is_parent = person("is_parent", period)

        # Get disability status
        p = parameters(
            period
        ).gov.dwp.pension_credit.guarantee_credit.child.disability

        eligible_based_on_disability = (
            add(
                person,
                period,
                p.eligibility + p.severe.eligibility,
            )
            > 0
        ) | (person("incapacity_benefit", period) > 0)

        # Count parents in benefit unit
        parent_count = add(benunit, period, ["is_parent"])
        has_children = benunit.any(benunit.members("is_child", period))

        # Eligibility conditions
        lone_parent_eligible = (
            (parent_count == 1) & has_children & in_work & is_parent
        )

        # Break out the complex nested conditions
        all_parents_working = benunit.all(where(is_parent, in_work, True))
        some_parents_working = benunit.any(in_work & is_parent)
        some_parents_disability_eligible = benunit.any(
            eligible_based_on_disability & is_parent
        )

        # Create a separate work condition
        couple_work_condition = all_parents_working | (
            some_parents_working & some_parents_disability_eligible
        )

        couple_eligible = (
            (parent_count == 2)
            & has_children
            & is_parent
            & couple_work_condition
        )

        return where(is_child, False, lone_parent_eligible | couple_eligible)
