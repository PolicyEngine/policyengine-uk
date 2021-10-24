from openfisca_uk.tools.general import *
from openfisca_uk.entities import *


class AFCS(Variable):
    value_type = float
    entity = Person
    label = u"Armed Forces Compensation Scheme"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("AA_reported", period)


class AFCS_reported(Variable):
    value_type = float
    entity = Person
    label = u"Armed Forces Compensation Scheme (reported)"
    definition_period = YEAR
