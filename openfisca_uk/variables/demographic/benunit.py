from openfisca_uk.variables.demographic.household import TenureType
from openfisca_uk.tools.general import *
from openfisca_uk.entities import *


class benunit_id(Variable):
    value_type = int
    entity = BenUnit
    label = u"ID for the family"
    definition_period = YEAR


class families(Variable):
    value_type = float
    entity = BenUnit
    label = u"Variable holding families"
    definition_period = YEAR
    default_value = 1


class benunit_weight(Variable):
    value_type = float
    entity = BenUnit
    label = u"Weight factor for the benefit unit"
    definition_period = YEAR


class is_married(Variable):
    value_type = bool
    entity = BenUnit
    label = "Married"
    documentation = "Whether the benefit unit adults are married to each other"
    definition_period = YEAR


class FamilyType(Enum):
    SINGLE = u"Single, with no children"
    COUPLE_NO_CHILDREN = u"Couple, with no children"
    LONE_PARENT = u"Lone parent, with children"
    COUPLE_WITH_CHILDREN = u"Couple, with children"


class RelationType(Enum):
    SINGLE = u"Single"
    COUPLE = u"Couple"


class family_type(Variable):
    value_type = Enum
    entity = BenUnit
    default_value = FamilyType.SINGLE
    possible_values = FamilyType
    label = u"Family composition"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        two_adults = benunit.sum(benunit.members("is_adult", period)) == 2
        has_children = benunit.sum(benunit.members("is_child", period)) > 0
        is_single = not_(two_adults) * not_(has_children)
        is_couple = two_adults * not_(has_children)
        is_lone = not_(two_adults) * has_children
        is_full = two_adults * has_children
        return select([is_single, is_couple, is_lone, is_full], FamilyType)


class relation_type(Variable):
    value_type = Enum
    entity = BenUnit
    default_value = RelationType.SINGLE
    possible_values = RelationType
    label = u"Whether single or a couple"
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
    label = u"Eldest adult age"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit.max(
            benunit.members("age", period.this_year), role=BenUnit.ADULT
        )


class youngest_adult_age(Variable):
    value_type = float
    entity = BenUnit
    label = u"Eldest adult age"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit.min(
            benunit.members("age", period.this_year), role=BenUnit.ADULT
        )


class eldest_child_age(Variable):
    value_type = float
    entity = BenUnit
    label = u"Eldest adult age"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit.max(
            benunit.members("age", period.this_year), role=BenUnit.CHILD
        )


class youngest_child_age(Variable):
    value_type = float
    entity = BenUnit
    label = u"Eldest adult age"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit.min(
            benunit.members("age", period.this_year), role=BenUnit.CHILD
        )


class num_children(Variable):
    value_type = int
    entity = BenUnit
    label = u"The number of children in the family"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("is_child", period))


class num_adults(Variable):
    value_type = int
    entity = BenUnit
    label = u"The number of adults in the family"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("is_adult", period))


class benunit_tenure_type(Variable):
    value_type = Enum
    possible_values = TenureType
    default_value = TenureType.RENT_PRIVATELY
    entity = BenUnit
    label = u"Tenure type of the family's household"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        tenure = benunit.value_from_first_person(
            benunit.members.household("tenure_type", period)
        )
        return tenure


class benunit_is_renting(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Whether this family is renting"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        tenure = benunit("benunit_tenure_type", period)
        return np.isin(
            tenure,
            (
                TenureType.RENT_PRIVATELY,
                TenureType.RENT_FROM_COUNCIL,
                TenureType.RENT_FROM_HA,
            ),
        )
