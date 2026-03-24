from policyengine_uk.model_api import *
import numpy as np


class household_land_value(Variable):
    entity = Household
    label = "Land value"
    documentation = "Estimated total land value directly owned by the household"
    unit = GBP
    definition_period = YEAR
    value_type = float
    quantity_type = STOCK

    def formula(household, period, parameters):
        region = household("region", period)
        Region = region.possible_values
        property_wealth = household("property_wealth", period)
        owned_land = household("owned_land", period)

        regional = (
            parameters(period)
            .household.wealth.land.intensity.property_wealth_by_region
        )

        property_wealth_intensity = np.select(
            [
                region == Region.LONDON,
                region == Region.SOUTH_EAST,
                region == Region.EAST_OF_ENGLAND,
                region == Region.SOUTH_WEST,
                region == Region.WEST_MIDLANDS,
                region == Region.EAST_MIDLANDS,
                region == Region.NORTH_WEST,
                region == Region.YORKSHIRE,
                region == Region.SCOTLAND,
                region == Region.WALES,
                region == Region.NORTH_EAST,
                region == Region.NORTHERN_IRELAND,
            ],
            [
                regional.LONDON,
                regional.SOUTH_EAST,
                regional.EAST_OF_ENGLAND,
                regional.SOUTH_WEST,
                regional.WEST_MIDLANDS,
                regional.EAST_MIDLANDS,
                regional.NORTH_WEST,
                regional.YORKSHIRE,
                regional.SCOTLAND,
                regional.WALES,
                regional.NORTH_EAST,
                regional.NORTHERN_IRELAND,
            ],
            default=regional.UNKNOWN,
        )

        return property_wealth * property_wealth_intensity + owned_land
