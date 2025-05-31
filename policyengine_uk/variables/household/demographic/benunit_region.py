from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.geography import Region


class benunit_region(Variable):
    label = "benefit unit region"
    entity = BenUnit
    definition_period = YEAR
    value_type = Enum
    possible_values = Region
    default_value = Region.LONDON

    def formula(benunit, period, parameters):
        return benunit.value_from_first_person(
            benunit.members.household("region", period)
        )
