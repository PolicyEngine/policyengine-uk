from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class winter_fuel_allowance_reported(Variable):
    value_type = float
    entity = Person
    label = u"Winter fuel allowance"
    definition_period = YEAR
