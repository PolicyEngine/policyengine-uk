from policyengine_uk.model_api import *


class domestic_rates(Variable):
    label = "domestic rates"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        rates = parameters(period).gov.local_authorities.domestic_rates.rates
        local_authority = household("local_authority", period)
        rate_defined = pd.Series(local_authority.decode_to_str()).isin(
            rates._children
        )
        percent = np.zeros(household.count, dtype=float)
        if any(rate_defined):
            percent[rate_defined] = rates[local_authority[rate_defined]]
            main_residence_value = household("main_residence_value", period)
            return percent * main_residence_value
        else:
            return 0
