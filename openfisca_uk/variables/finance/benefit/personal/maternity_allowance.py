from openfisca_uk.tools.general import *
from openfisca_uk.entities import *


class maternity_allowance_reported(Variable):
    value_type = float
    entity = Person
    label = u"Maternity allowance"
    definition_period = YEAR
