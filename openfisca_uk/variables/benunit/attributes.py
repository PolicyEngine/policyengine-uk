from openfisca_core.model_api import *
from openfisca_uk.entities import *
import numpy as np

class benunit_weight(Variable):
    value_type = float
    entity = BenUnit
    label = u'label'
    definition_period = ETERNITY

class benunit_equivalisation(Variable):
    value_type = float
    entity = BenUnit
    label = u'label'
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        second_adult = benunit.nb_persons(benunit.ADULT) == 2
        num_young_children = benunit.sum(
            benunit.members("is_young_child", period)
        )
        num_older_children = benunit.sum(
            benunit.members("is_older_child", period)
        )
        weighting = (
            0.67
            + 0.33 * second_adult
            + 0.33 * num_older_children
            + 0.2 * num_young_children
        )
        return weighting

class younger_adult_age(Variable):
    value_type = int
    entity = BenUnit
    label = u"Minimum age of an adult in the benunit"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.min(max_(benunit.members("age", period), 16))


class older_adult_age(Variable):
    value_type = int
    entity = BenUnit
    label = u"Maximum age of an adult in the benunit"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.max(max_(benunit.members("age", period), 16))

class is_lone_parent(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Whether the benunit structure is a lone parent"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return (benunit.nb_persons(BenUnit.ADULT) == 1) * (
            benunit.nb_persons(BenUnit.CHILD) > 0
        )


class is_couple(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Whether the benunit structure is a lone parent"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.nb_persons(BenUnit.ADULT) == 2


class is_single(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Whether the benunit structure is a lone parent"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return (benunit.nb_persons(BenUnit.ADULT) == 1) * (
            benunit.nb_persons(BenUnit.CHILD) == 0
        )