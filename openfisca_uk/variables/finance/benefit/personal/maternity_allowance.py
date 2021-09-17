from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class maternity_allowance_reported(Variable):
    value_type = float
    entity = Person
    label = u"Maternity allowance"
    definition_period = YEAR
