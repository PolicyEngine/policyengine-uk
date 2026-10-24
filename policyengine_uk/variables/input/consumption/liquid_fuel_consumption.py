from policyengine_uk.model_api import *

# COICOP 04.5.3 (liquid fuels). A sub-component of
# housing_water_and_electricity_consumption (COICOP 04), so not added into the
# `consumption` total, which already counts it. Liquefied petroleum gas
# (bottled butane and propane) is not a liquid fuel in COICOP: it is gas
# (04.5.2; liquefied hydrocarbons, 04.5.2.2, in COICOP 2018). Microcosm UK
# maps ONS 04.5.3 to liquid fuels and keeps the LCF's bottled gas (b018,
# c45222) in the housing remainder, so the two agree.


class liquid_fuel_consumption(Variable):
    label = "Liquid fuel consumption"
    documentation = (
        "Annual household spending on liquid fuels, chiefly heating oil and "
        "other domestic fuel oils (COICOP 04.5.3), mostly for heating homes "
        "off the gas grid. It excludes liquefied petroleum gas (bottled gas), "
        "which COICOP classes as gas (04.5.2). Already included in "
        "housing_water_and_electricity_consumption; do not add it to "
        "consumption again. Dataset projection uprates it by CPI from the data "
        "year, like other LCFS spending: Ofgem's price cap, which prices the "
        "electricity and gas inputs, does not cover it."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW
    reference = "https://unstats.un.org/unsd/classifications/unsdclassifications/COICOP_2018_-_pre-edited_white_cover_version_-_2018-12-26.pdf"
    uprating = "gov.economic_assumptions.indices.obr.consumer_price_index"
