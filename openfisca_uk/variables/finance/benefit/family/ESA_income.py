from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class ESA_income_reported(Variable):
    value_type = float
    entity = Person
    label = u"ESA (income-based) (reported amount per week)"
    definition_period = WEEK

class ESA_income(Variable):
    value_type = float
    entity = BenUnit
    label = u"ESA (income-based)"
    definition_period = WEEK

    def formula(benunit, period, parameters):
        return aggr(benunit, period, ["ESA_income_reported"])
