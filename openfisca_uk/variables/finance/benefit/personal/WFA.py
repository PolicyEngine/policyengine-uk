from openfisca_uk.model_api import *


class winter_fuel_allowance_reported(Variable):
    value_type = float
    entity = Person
    label = u"Winter fuel allowance"
    definition_period = YEAR
    unit = "currency-GBP"
