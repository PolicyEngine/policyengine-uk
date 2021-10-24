from openfisca_uk.tools.general import *
from openfisca_uk.entities import *


class student_loans(Variable):
    value_type = float
    entity = Person
    label = u"Student loans"
    definition_period = YEAR


class student_payments(Variable):
    value_type = float
    entity = Person
    label = u"Student payments"
    definition_period = YEAR
