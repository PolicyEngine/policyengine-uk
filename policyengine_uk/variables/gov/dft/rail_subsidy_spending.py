from policyengine_uk.model_api import *


class rail_subsidy_spending(Variable):
    label = "rail subsidy spending"
    documentation = (
        "Total spending on rail subsidies for this household. "
        "Computed as rail_usage × fare_index, allowing reforms to "
        "modify fare prices independently of usage quantity."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        # Get rail usage (quantity at base year prices)
        # This should be provided by policyengine-uk-data
        rail_usage = household("rail_usage", period)

        # Get the fare index for the current period
        fare_index = parameters(period).gov.dft.rail.fare_index

        # Spending = quantity × price
        return rail_usage * fare_index
