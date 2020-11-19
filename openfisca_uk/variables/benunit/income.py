from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class benunit_earnings(Variable):
    value_type = float
    entity = BenUnit
    label = u"Earned income by the benefit unit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("earned_income", period))


class benunit_post_tax_income(Variable):
    value_type = float
    entity = BenUnit
    label = u"Post-tax income for the benefit unit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("post_tax_income", period))

class benunit_net_income(Variable):
    value_type = float
    entity = BenUnit
    label = u'FRS net income'
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return aggr(benunit, period, ["net_income"])