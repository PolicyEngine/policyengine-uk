from policyengine_uk.model_api import *


class FamilyType(Enum):
    SINGLE = "Single, with no children"
    COUPLE_NO_CHILDREN = "Couple, with no children"
    LONE_PARENT = "Lone parent, with children"
    COUPLE_WITH_CHILDREN = "Couple, with children"


class family_type(Variable):
    value_type = Enum
    entity = BenUnit
    default_value = FamilyType.SINGLE
    possible_values = FamilyType
    label = "Family composition by age 18 (deprecated)"
    documentation = (
        "Deprecated: an age cut-off with no legal basis, kept only for "
        "downstream compatibility with its original formula. Nothing in "
        "policyengine-uk uses it. Use relation_type with the programme's own responsibility for a child or young person (for example is_lone_parent for the legacy benefits), or hbai_person_type for HBAI statistics instead."
    )
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
