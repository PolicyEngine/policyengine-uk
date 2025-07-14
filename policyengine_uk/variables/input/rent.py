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

        private_rent_uprating = obr.lagged_average_earnings(
            period
        ) / obr.lagged_average_earnings(data_year)
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
