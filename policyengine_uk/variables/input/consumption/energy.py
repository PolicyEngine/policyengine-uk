from policyengine_uk.model_api import *

label = "Energy"
description = "Energy consumption."


class domestic_energy_consumption(Variable):
    label = "Domestic energy consumption"
    documentation = "Combined gas and electric bills."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.consumer_price_index"


class electricity_consumption(Variable):
    label = "Electricity consumption"
    documentation = "Annual household electricity spending, imputed from LCFS and calibrated to NEED 2023 admin data."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.consumer_price_index"


class gas_consumption(Variable):
    label = "Gas consumption"
    documentation = "Annual household gas spending, imputed from LCFS and calibrated to NEED 2023 admin data."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.consumer_price_index"
