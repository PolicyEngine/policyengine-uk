from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class ESA_income_reported(Variable):
    value_type = float
    entity = Person
    label = u"ESA (income-based) (reported amount)"
    definition_period = YEAR


class ESA_income(Variable):
    value_type = float
    entity = BenUnit
    label = u"ESA (income-based)"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return aggr(benunit, period, ["ESA_income_reported"])
