from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class disabled_adults(Variable):
    value_type = int
    entity = BenUnit
    label = u"Number of disabled adults in the benefit unit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit.sum(
            benunit.members("is_disabled", period), role=BenUnit.ADULT
        )


class disabled_children(Variable):
    value_type = int
    entity = BenUnit
    label = u"Number of disabled children in the benefit unit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit.sum(
            benunit.members("is_disabled", period), role=BenUnit.CHILD
        )


class severely_disabled_adults(Variable):
    value_type = int
    entity = BenUnit
    label = u"Number of severely disabled adults in the benefit unit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit.sum(
            benunit.members("is_severely_disabled", period), role=BenUnit.ADULT
        )


class severely_disabled_children(Variable):
    value_type = int
    entity = BenUnit
    label = u"Number of severely disabled children in the benefit unit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit.sum(
            benunit.members("is_severely_disabled", period), role=BenUnit.CHILD
        )


class enhanced_disabled_adults(Variable):
    value_type = int
    entity = BenUnit
    label = u"Number of enhanced disabled adults in the benefit unit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit.sum(
            benunit.members("is_enhanced_disabled", period), role=BenUnit.ADULT
        )


class enhanced_disabled_children(Variable):
    value_type = int
    entity = BenUnit
    label = u"Number of enhanced disabled children in the benefit unit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit.sum(
            benunit.members("is_enhanced_disabled", period), role=BenUnit.CHILD
        )


class has_carer(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Whether there is a carer in the benefit unit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("is_carer", period))
