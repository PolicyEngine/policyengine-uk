from openfisca_uk.model_api import *


class maternity_allowance_reported(Variable):
    value_type = float
    entity = Person
    label = u"Maternity allowance"
    definition_period = YEAR
    unit = "currency-GBP"
