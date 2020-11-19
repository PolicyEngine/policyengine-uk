from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class benunit_income_tax(Variable):
    value_type = float
    entity = BenUnit
    label = u"Income Tax paid by the benefit unit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return aggr(benunit, period, ["income_tax"])

class benunit_tax(Variable):
    value_type = float
    entity = BenUnit
    label = u'Total tax paid by the benefit unit'
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return aggr(benunit, period, ["total_tax"])