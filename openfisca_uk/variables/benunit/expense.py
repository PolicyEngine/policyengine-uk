from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class benunit_pension_deductions(Variable):
    value_type = float
    entity = BenUnit
    label = u"Pension contributions by the benefit unit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("pension_deductions", period))


class benunit_rent(Variable):
    value_type = float
    entity = BenUnit
    label = u"Total benefit unit rental costs"
    definition_period = WEEK
    set_input = set_input_divide_by_period

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("personal_rent", period))
