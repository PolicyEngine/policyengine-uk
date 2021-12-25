from openfisca_uk.model_api import *


class student_loans(Variable):
    value_type = float
    entity = Person
    label = u"Student loans"
    definition_period = YEAR
    unit = "currency-GBP"


class student_payments(Variable):
    value_type = float
    entity = Person
    label = u"Student payments"
    definition_period = YEAR
    unit = "currency-GBP"
