from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *

class rent(Variable):
    value_type = float
    entity = Household
    label = u'Gross rent for the household'
    definition_period = YEAR