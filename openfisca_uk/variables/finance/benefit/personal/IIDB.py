from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class IIDB(Variable):
    value_type = float
    entity = Person
    label = u"Industrial Injuries Disablement Benefit"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("IIDB_reported", period)


class IIDB_reported(Variable):
    value_type = float
    entity = Person
    label = u"Industrial Injuries Disablement Benefit (reported)"
    definition_period = YEAR
