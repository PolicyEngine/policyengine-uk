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
        # Only apply uprating for microsimulation datasets
        if household.simulation.dataset is None:
            return 0

        data_year = household.simulation.dataset.time_period

        # Don't apply formula for years at or before data year
        # The data itself contains the rent values for those years
        if period.start.year <= data_year:
            return 0

        if period.start.year < 2023:
            # We don't have growth rates for rent before this.
            return 0

        # For future years after the data year, uprate from data year
        # Get rent directly from holder to avoid recursion
        holder = household.get_holder("rent")
        original_rent = holder.get_array(data_year)
        if original_rent is None:
            return 0
        tenure_type = household("tenure_type", period).decode_to_str()

        is_social_rent = (tenure_type == "RENT_FROM_COUNCIL") | (
            tenure_type == "RENT_FROM_HA"
        )

        is_private_rent = tenure_type == "RENT_PRIVATELY"

        p = parameters.gov.economic_assumptions.indices.obr

        private_rent_uprating = p.lagged_average_earnings(
            period
        ) / p.lagged_average_earnings(data_year)
        social_rent_uprating = p.social_rent(period) / p.social_rent(data_year)

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
