from policyengine_uk.model_api import *


class rent(Variable):
    label = "Rent"
    documentation = (
        "The total amount of rent paid by the household in the year."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW

    def formula(household, period, parameters):
        if period.start.year < 2023:
            # We don't have growth rates for rent before this.
            return 0

        if household.simulation.dataset is None:
            return 0

        data_year = household.simulation.dataset.time_period
        original_rent = household("rent", data_year)
        tenure_type = household("tenure_type", period).decode_to_str()

        is_social_rent = (tenure_type == "RENT_FROM_COUNCIL") | (
            tenure_type == "RENT_FROM_HA"
        )

        is_private_rent = tenure_type == "RENT_PRIVATELY"

        obr = parameters.gov.economic_assumptions.indices.obr

        # Get regional private rent indices
        region_str = household("region", period).decode_to_str()
        regional_private_rent = (
            parameters.gov.economic_assumptions.indices.ons.private_rental_prices
        )

        # Default to OBR private rent growth for all households
        private_rent_uprating = obr.private_rent(period) / obr.private_rent(data_year)

        # Try to use regional data where available
        region_name = region_str.item()
        if region_name == "UNKNOWN":
            region_name = "UNITED_KINGDOM"
        if hasattr(regional_private_rent, region_name):
            regional_index = getattr(regional_private_rent, region_name)
            
            # We don't have ONS private rental price indices beyond 2024
            if period.start.year > 2024:
                # Splice regional indices (data_year to 2024) with private rent forecast (2024 to period)
                regional_uprating = regional_index(2024) / regional_index(data_year)
                forecast_uprating = obr.private_rent(period) / obr.private_rent(2024)
                private_rent_uprating = regional_uprating * forecast_uprating
            else:
                private_rent_uprating = regional_index(period) / regional_index(data_year)

        social_rent_uprating = obr.social_rent(period) / obr.social_rent(
            data_year
        )

        return select(
            [
                is_social_rent,
                is_private_rent,
                True,
            ],
            [
                original_rent * social_rent_uprating,
                original_rent * private_rent_uprating,
                original_rent,
            ],
        )
