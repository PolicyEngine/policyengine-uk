from policyengine_uk.model_api import *


class rail_subsidy_spending(Variable):
    label = "rail subsidy spending"
    documentation = (
        "Total spending on rail subsidies for this household. "
        "Computed as rail fare index × rail usage to properly separate "
        "price (fare changes) from quantity (ridership changes)."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        # Get the rail usage quantity (uprated by ridership growth)
        rail_usage = household("rail_usage", period)

        # Get the fare index for the current period
        fare_index = parameters(period).gov.dft.rail.fare_index

        # Base year fare index (2020)
        base_fare_index = 1.0

        # Scale usage by the relative change in fares
        # This ensures spending reflects both quantity and price changes
        fare_multiplier = fare_index / base_fare_index

        return rail_usage * fare_multiplier
