from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class council_tax_benefit_reported(Variable):
    value_type = float
    entity = Person
    label = u"CTB (reported)"
    definition_period = YEAR
    reference = ""


class council_tax_benefit(Variable):
    value_type = float
    entity = BenUnit
    label = u"CTB"
    definition_period = YEAR
    reference = ""

    def formula(benunit, period, parameters):
        return aggr(benunit, period, ["council_tax_benefit_reported"])
