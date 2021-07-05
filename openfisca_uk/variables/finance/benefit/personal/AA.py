from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class AA(Variable):
    value_type = float
    entity = Person
    label = u"Attendance Allowance"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("AA_reported", period)


class AA_reported(Variable):
    value_type = float
    entity = Person
    label = u"Attendance Allowance (reported)"
    definition_period = YEAR
