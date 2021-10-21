from openfisca_uk.tools.general import *
from openfisca_uk.entities import *


class winter_fuel_allowance_reported(Variable):
    value_type = float
    entity = Person
    label = u"Winter fuel allowance"
    definition_period = YEAR
