from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class pension_credit_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported amount of Pension Credit per week"
    definition_period = WEEK
