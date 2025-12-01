from policyengine_uk.model_api import *


class owns_vehicle(Variable):
    label = "whether the household owns a vehicle"
    documentation = (
        "Used for calibration to NTS 2024 data "
        "showing 78% of UK households own at least one car. "
        "Source: https://www.gov.uk/government/statistics/national-travel-survey-2024"
    )
    reference = "https://www.gov.uk/government/statistics/national-travel-survey-2024/nts-2024-household-car-availability-and-trends-in-car-trips"
    entity = Household
    definition_period = YEAR
    value_type = bool

    def formula(household, period):
        return household("num_vehicles", period) > 0
