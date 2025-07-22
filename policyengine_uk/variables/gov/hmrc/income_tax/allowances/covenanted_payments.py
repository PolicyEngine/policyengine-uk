from policyengine_uk.model_api import *


class covenanted_payments(Variable):
    value_type = float
    entity = Person
    label = "Covenanted payments to charities"
    definition_period = YEAR
    unit = GBP
