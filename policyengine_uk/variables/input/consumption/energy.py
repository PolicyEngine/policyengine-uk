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
    uprating = "gov.economic_assumptions.energy_prices.fiscal_year.electricity_gas_and_solid_fuels"


class electricity_consumption(Variable):
    label = "Electricity consumption"
    documentation = "Annual household electricity spending, imputed from LCFS and calibrated to NEED 2023 admin data."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    uprating = "gov.economic_assumptions.energy_prices.fiscal_year.electricity"


class gas_consumption(Variable):
    label = "Gas consumption"
    documentation = "Annual household gas spending, imputed from LCFS and calibrated to NEED 2023 admin data."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    uprating = "gov.economic_assumptions.energy_prices.fiscal_year.gas"


class uses_energy_prepayment_meter(Variable):
    label = "Uses an energy prepayment meter"
    documentation = (
        "Whether the household pays for domestic gas or electricity through "
        "a prepayment meter. Current PolicyEngine UK microsimulation data does "
        "not populate this input, so it defaults to false unless supplied in a "
        "household calculation or by a future dataset."
    )
    entity = Household
    definition_period = YEAR
    value_type = bool
