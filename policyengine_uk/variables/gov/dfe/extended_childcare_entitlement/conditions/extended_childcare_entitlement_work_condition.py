from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.benunit import FamilyType


class extended_childcare_entitlement_work_condition(Variable):
    value_type = bool
    entity = Person
    label = "Work conditions for extended childcare entitlement"
    documentation = "Whether the person/couple meets work requirements for extended childcare entitlement"
    definition_period = YEAR

    def formula(person, period, parameters):
        benunit = person.benunit
        family_type = benunit("family_type", period)
        age = person("age", period)
        is_child = person("is_child", period)
        in_work = person("in_work", period)

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

        # Check if person is among two oldest
        benunit_ages = benunit.members("age", period)
        first_highest = benunit.max(benunit_ages)
        is_among_two_oldest = (age == first_highest) | (
            age
            == benunit.max(
                where(benunit_ages < first_highest, benunit_ages, -inf)
            )
        )

        # Eligibility conditions
        lone_parent_eligible = (
            (family_type == FamilyType.LONE_PARENT)
            & in_work
            & (age == first_highest)
        )

        couple_eligible = (
            (family_type == FamilyType.COUPLE_WITH_CHILDREN)
            & is_among_two_oldest
            & (
                benunit.all(where(is_among_two_oldest, in_work, True))
                | (
                    benunit.any(in_work & is_among_two_oldest)
                    & benunit.any(
                        eligible_based_on_disability & is_among_two_oldest
                    )
                )
            )
        )

        return where(is_child, False, lone_parent_eligible | couple_eligible)
