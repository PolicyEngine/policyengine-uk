from policyengine_uk.model_api import *


class sdlt_liable(Variable):
    label = "Liable for Stamp Duty"
    documentation = "Whether the household is liable for Stamp Duty Land Tax"
    entity = Household
    definition_period = YEAR
    value_type = bool
    unit = GBP

    def formula(household, period):
        country = household("country", period)
        countries = country.possible_values
        return np.isin(
            country.decode_to_str(),
            [countries.ENGLAND.name, countries.NORTHERN_IRELAND.name],
        )
