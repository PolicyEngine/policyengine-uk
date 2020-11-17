from openfisca_core.model_api import *
from openfisca_uk.entities import *

class pension_contrib(Variable):
    value_type = float
    entity = Person
    label = u'Pension contributions'
    definition_period = YEAR

class childcare(Variable):
    value_type = float
    entity = Person
    label = u'Childcare costs'
    definition_period = YEAR