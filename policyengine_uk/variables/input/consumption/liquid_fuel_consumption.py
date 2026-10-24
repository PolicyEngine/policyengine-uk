from policyengine_uk.model_api import *

# Heating oil, paraffin and bottled gas (COICOP 04.5.3 and part of 04.5.2).
# A sub-component of housing_water_and_electricity_consumption (COICOP 04),
# so not added into the `consumption` total, which already counts it.


class liquid_fuel_consumption(Variable):
    label = "Liquid fuel consumption"
    documentation = (
        "Annual household spending on heating oil, paraffin and bottled gas, "
        "mostly for heating homes off the gas grid. COICOP puts bottled gas "
        "(liquefied petroleum gas) under 04.5.2, gas, so a dataset that includes "
        "it is wider than ONS's 04.5.3. Microcosm's frame includes bottled gas "
        "and does not level this column to ONS Consumer Trends 04.5.3. A "
        "costing using this input needs levelling to ONS first, accounting for "
        "the bottled gas separately. No model formula reads this input yet. "
        "Already included in "
        "housing_water_and_electricity_consumption; do not add it to "
        "consumption again. Dataset projection uprates it by CPI from the data "
        "year, like other LCFS spending: Ofgem's price cap, which prices the "
        "electricity and gas inputs, does not cover it."
    )
    reference = (
        "https://unstats.un.org/unsd/classifications/Econ/Structure/Detail/EN/2094/04_5_2",
        "https://unstats.un.org/unsd/classifications/Econ/Structure/Detail/EN/2094/04_5_3",
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW
    uprating = "gov.economic_assumptions.indices.obr.consumer_price_index"
