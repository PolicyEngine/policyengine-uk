from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.geography import Region


class is_renting(Variable):
    value_type = bool
    entity = Household
    label = "Is renting"
    definition_period = YEAR

    def formula(household, period, parameters):
        tenure = household("tenure_type", period)
        tenures = tenure.possible_values
        RENT_TENURES = [
            tenures.RENT_PRIVATELY,
            tenures.RENT_FROM_COUNCIL,
            tenures.RENT_PRIVATELY,
        ]
        return is_in(tenure, RENT_TENURES)
