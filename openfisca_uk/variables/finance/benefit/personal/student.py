from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class student_loans(Variable):
    value_type = float
    entity = Person
    label = u"label"
    definition_period = YEAR
    reference = ""


class student_payments(Variable):
    value_type = float
    entity = Person
    label = u"label"
    definition_period = YEAR
    reference = ""
