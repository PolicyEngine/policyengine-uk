from openfisca_uk.model_api import *


class country_id(Variable):
    label = "Country ID"
    documentation = "Identity of the country"
    entity = Country
    definition_period = ETERNITY
    value_type = int


class country_weight(Variable):
    label = "Country weight"
    documentation = "Number of countries represented"
    entity = Country
    definition_period = ETERNITY
    value_type = float
