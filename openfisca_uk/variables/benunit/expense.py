from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class benunit_pension_contributions(Variable):
    value_type = float
    entity = BenUnit
    label = u"Pension contributions by the benefit unit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("pension_contributions", period))

class benunit_rent(Variable):
    value_type = float
    entity = BenUnit
    label = u'Total benefit unit rental costs'
    definition_period = WEEK

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("personal_rent", period))

class benunit_housing_costs(Variable):
    value_type = float
    entity = BenUnit
    label = u'Total benefit unit rental costs'
    definition_period = WEEK

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("personal_housing_costs", period))