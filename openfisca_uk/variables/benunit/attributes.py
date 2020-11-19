from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class is_married(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Whether the benefit unit adults are married"
    definition_period = ETERNITY


class FamilyType(Enum):
    SINGLE = u"Single, with no children"
    COUPLE_NO_KIDS = u"Couple, with no children"
    LONE_PARENT = u"Lone parent, with children"
    COUPLE_KIDS = u"Couple, with children"


class family_type(Variable):
    value_type = Enum
    entity = BenUnit
    default_value = FamilyType.SINGLE
    possible_values = FamilyType
    label = u"Family composition"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        two_adults = benunit.nb_persons(BenUnit.ADULT) == 2
        has_children = benunit.nb_persons(BenUnit.CHILD) > 0
        is_single = not_(two_adults) * not_(has_children)
        is_couple = two_adults * not_(has_children)
        is_lone = not_(two_adults) * has_children
        is_full = two_adults * has_children
        return select([is_single, is_couple, is_lone, is_full], FamilyType)


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


class is_single(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Whether is a single adult"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.nb_persons(BenUnit.ADULT) == 1


class is_couple(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Whether is a couple"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.nb_persons(BenUnit.ADULT) == 2


class has_children(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Whether children are in the benefit unit"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.nb_persons(BenUnit.CHILD) > 0


class is_lone_parent(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Whether is a lone parent"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit("is_single") * benunit("has_children")


class is_couple_parents(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Whether is a couple with children"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit("is_couple") * benunit("has_children")


class is_childless_couple(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Whether is a couple without children"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit("is_couple") * not_(benunit("has_children"))


class is_single_person(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Whether is a single adult"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit("is_single") * not_(benunit("has_children"))


class benunit_weight(Variable):
    value_type = float
    entity = BenUnit
    label = u"Weighting of the benefit unit"
    definition_period = ETERNITY


class benunit_id(Variable):
    value_type = str
    entity = BenUnit
    label = u"ID of the benefit unit"
    definition_period = ETERNITY

class benunit_SP_age(Variable):
    value_type = bool
    entity = BenUnit
    label = u'Whether either member of the benefit unit is State Pension age'
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit.max(benunit.members("is_SP_age", period))