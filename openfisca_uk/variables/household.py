from openfisca_core.model_api import *
from openfisca_uk.entities import *

class household_weight(Variable):
    value_type = float
    entity = Household
    label = u'FRS weighting of the household'
    definition_period = ETERNITY