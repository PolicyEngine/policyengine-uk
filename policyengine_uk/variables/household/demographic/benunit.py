from policyengine_uk.variables.household.demographic.household import (
    TenureType,
)
from policyengine_uk.model_api import *


class benunit_id(Variable):
    value_type = int
    entity = BenUnit
    label = "ID for the family"
    definition_period = YEAR


class families(Variable):
    value_type = float
    entity = BenUnit
    label = "Variable holding families"
    definition_period = YEAR
    default_value = 1


class benunit_weight(Variable):
    value_type = float
    entity = BenUnit
    label = "Weight factor for the benefit unit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit.max(benunit.members("person_weight", period))


class is_married(Variable):
    value_type = bool
    entity = BenUnit
    label = "Married"
    documentation = "Whether the benefit unit adults are married to each other or in a civil partnership"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return add(benunit, period, ["is_adult"]) == 2


class FamilyType(Enum):
    SINGLE = "Single, with no children"
    COUPLE_NO_CHILDREN = "Couple, with no children"
    LONE_PARENT = "Lone parent, with children"
    COUPLE_WITH_CHILDREN = "Couple, with children"


class RelationType(Enum):
    SINGLE = "Single"
    COUPLE = "Couple"


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


class relation_type(Variable):
    value_type = Enum
    entity = BenUnit
    default_value = RelationType.SINGLE
    possible_values = RelationType
    label = "Whether single or a couple"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return where(
            benunit.sum(benunit.members("is_adult", period)) == 1,
            RelationType.SINGLE,
            RelationType.COUPLE,
        )


class eldest_adult_age(Variable):
    value_type = float
    entity = BenUnit
    label = "Eldest adult age"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit.max(
            where(
                benunit.members("is_adult", period),
                benunit.members("age", period),
                -np.inf,
            )
        )


class youngest_adult_age(Variable):
    value_type = float
    entity = BenUnit
    label = "Eldest adult age"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit.min(
            where(
                benunit.members("is_adult", period),
                benunit.members("age", period),
                np.inf,
            )
        )


class eldest_child_age(Variable):
    value_type = float
    entity = BenUnit
    label = "Eldest adult age"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit.max(
            where(
                benunit.members("is_child", period),
                benunit.members("age", period),
                -np.inf,
            )
        )


class youngest_child_age(Variable):
    value_type = float
    entity = BenUnit
    label = "Eldest adult age"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit.min(
            where(
                benunit.members("is_child", period),
                benunit.members("age", period),
                np.inf,
            )
        )


class num_children(Variable):
    value_type = int
    entity = BenUnit
    label = "The number of children in the family"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("is_child", period))


class num_adults(Variable):
    value_type = int
    entity = BenUnit
    label = "The number of adults in the family"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("is_adult", period))


class benunit_tenure_type(Variable):
    value_type = Enum
    possible_values = TenureType
    default_value = TenureType.RENT_PRIVATELY
    entity = BenUnit
    label = "Tenure type of the family's household"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit.value_from_first_person(
            benunit.members.household("tenure_type", period)
        )


class benunit_is_renting(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether this family is renting"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        tenure = benunit("benunit_tenure_type", period)
        tenures = tenure.possible_values
        RENT_TENURES = [
            tenures.RENT_PRIVATELY,
            tenures.RENT_FROM_COUNCIL,
            tenures.RENT_FROM_HA,
        ]
        return np.isin(tenure, RENT_TENURES)
