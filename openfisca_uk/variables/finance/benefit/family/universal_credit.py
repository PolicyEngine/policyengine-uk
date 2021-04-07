from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *

class universal_credit_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported amount of Universal Credit per month"
    definition_period = WEEK