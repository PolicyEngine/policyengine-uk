"""Carbon intensities of household spending."""

# The spending categories consumption adds, in the order carbon_consumption
# sums them.
CARBON_CATEGORIES = [
    "food_and_non_alcoholic_beverages_consumption",
    "alcohol_and_tobacco_consumption",
    "clothing_and_footwear_consumption",
    "housing_water_and_electricity_consumption",
    "household_furnishings_consumption",
    "health_consumption",
    "transport_consumption",
    "communication_consumption",
    "recreation_consumption",
    "education_consumption",
    "restaurants_and_hotels_consumption",
    "miscellaneous_consumption",
]


def carbon_intensities(parameters, period) -> list:
    """Tonnes of CO2 per pound spent in each of CARBON_CATEGORIES: the
    published emissions of its sector over the published spending on it, or
    the parameter intensity where that spending is zero."""
    consumption = parameters(period).household.consumption
    aggregate_spending_by_sector = [
        consumption.total_by_category[category] for category in CARBON_CATEGORIES
    ]
    carbon = consumption.carbon
    aggregate_emissions_by_sector = [
        carbon.emissions[category.replace("_consumption", "")]
        for category in CARBON_CATEGORIES
    ]
    return [
        emissions / spending if spending > 0 else carbon.intensity[name]
        for emissions, spending, name in zip(
            aggregate_emissions_by_sector,
            aggregate_spending_by_sector,
            CARBON_CATEGORIES,
        )
    ]


def published_emissions(parameters, period) -> float:
    """The published emissions of all of CARBON_CATEGORIES' sectors."""
    carbon = parameters(period).household.consumption.carbon
    return sum(
        carbon.emissions[category.replace("_consumption", "")]
        for category in CARBON_CATEGORIES
    )
