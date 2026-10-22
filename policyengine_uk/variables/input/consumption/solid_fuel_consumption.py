from policyengine_uk.model_api import *

# COICOP 04.5.4 (solid fuels). A sub-component of
# housing_water_and_electricity_consumption (COICOP 04), so not added into the
# `consumption` total, which already counts it.


class solid_fuel_consumption(Variable):
    label = "Solid fuel consumption"
    documentation = (
        "Annual household spending on solid fuels such as coal, smokeless fuel "
        "and wood (COICOP 04.5.4), mostly for heating homes off the gas grid. "
        "Already included in housing_water_and_electricity_consumption; do not "
        "add it to consumption again. Dataset projection uprates it by CPI from "
        "the data year, like other LCFS spending: Ofgem's price cap, which "
        "prices the electricity and gas inputs, does not cover it."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW
    uprating = "gov.economic_assumptions.indices.obr.consumer_price_index"
