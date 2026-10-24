from policyengine_uk.model_api import *

# COICOP 04.5.4 (solid fuels). A sub-component of
# housing_water_and_electricity_consumption (COICOP 04), so not added into the
# `consumption` total, which already counts it.


class solid_fuel_consumption(Variable):
    label = "Solid fuel consumption"
    documentation = (
        "Annual household spending on solid fuels such as coal, smokeless fuel "
        "and wood (COICOP 04.5.4), mostly for heating homes off the gas grid. "
        "Microcosm's frame does not level this column to ONS Consumer Trends "
        "04.5.4. A costing using this input needs levelling to ONS first. No "
        "model formula reads this input yet. "
        "Already included in housing_water_and_electricity_consumption; do not "
        "add it to consumption again. Dataset projection uprates it by CPI from "
        "the data year, like other LCFS spending: Ofgem's price cap, which "
        "prices the electricity and gas inputs, does not cover it."
    )
    reference = "https://unstats.un.org/unsd/classifications/Econ/Structure/Detail/EN/2094/04_5_4"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW
    uprating = "gov.economic_assumptions.indices.obr.consumer_price_index"
