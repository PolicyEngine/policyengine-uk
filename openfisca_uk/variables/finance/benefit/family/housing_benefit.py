from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *

class housing_benefit_reported(Variable):
    value_type = float
    entity = Person
    label = u"Housing Benefit (reported amount per week)"
    definition_period = WEEK