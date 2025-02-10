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
        eligible_based_on_disability = (
            add(
                person,
                period,
                parameters(
                    period
                ).gov.dwp.pension_credit.guarantee_credit.child.disability.eligibility
                + parameters(
                    period
                ).gov.dwp.pension_credit.guarantee_credit.child.disability.severe.eligibility,
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

        couple_eligible = (
            (parent_count == 2)
            & has_children
            & is_parent
            & (
                benunit.all(where(is_parent, in_work, True))
                | (
                    benunit.any(in_work & is_parent)
                    & benunit.any(eligible_based_on_disability & is_parent)
                )
            )
        )

        return where(is_child, False, lone_parent_eligible | couple_eligible)
