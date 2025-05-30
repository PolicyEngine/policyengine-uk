from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.geography import Region


class household_count_people(Variable):
    value_type = int
    entity = Household
    label = "Number of people"
    definition_period = YEAR
    unit = "person"

    def formula(household, period, parameters):
        return household.nb_persons()
