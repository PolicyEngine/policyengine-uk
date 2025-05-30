from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.geography import Region


class country(Variable):
    value_type = Enum
    possible_values = Country
    default_value = Country.ENGLAND
    entity = Household
    label = "Country of the UK"
    definition_period = YEAR

    def formula(household, period, parameters):
        region = household("region", period)
        return select(
            [
                region == Region.UNKNOWN,
                region == Region.SCOTLAND,
                region == Region.WALES,
                region == Region.NORTHERN_IRELAND,
            ],
            [
                Country.UNKNOWN,
                Country.SCOTLAND,
                Country.WALES,
                Country.NORTHERN_IRELAND,
            ],
            default=Country.ENGLAND,
        )
