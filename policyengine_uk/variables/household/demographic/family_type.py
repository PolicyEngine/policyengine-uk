from policyengine_uk.variables.household.demographic.household import (

class family_type(Variable):
    value_type = Enum
    entity = BenUnit
    default_value = FamilyType.SINGLE
    possible_values = FamilyType
    label = "Family composition"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        two_adults = add(benunit, period, ["is_adult"]) == 2
        has_children = benunit.any(benunit.members("is_child", period))
        single = ~two_adults & ~has_children
        couple_no_children = two_adults & ~has_children
        lone_parent = ~two_adults & has_children
        couple_with_children = two_adults & has_children
        return select(
            [single, couple_no_children, lone_parent, couple_with_children],
            FamilyType,
        )
