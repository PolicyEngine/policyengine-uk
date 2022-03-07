from openfisca_uk.model_api import *


class housing_benefit_reported(Variable):
    value_type = float
    entity = Person
    label = "Housing Benefit (reported amount)"
    definition_period = YEAR
    unit = "currency-GBP"
