from openfisca_uk.model_api import *


@uprated(by="gov.ofgem.price_cap.base")
class domestic_energy_consumption(Variable):
    label = "Domestic energy consumption"
    documentation = "Combined gas and electric bills."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
