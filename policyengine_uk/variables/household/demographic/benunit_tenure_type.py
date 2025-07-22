from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.tenure_type import (
    TenureType,
)


class benunit_tenure_type(Variable):
    value_type = Enum
    possible_values = TenureType
    default_value = TenureType.RENT_PRIVATELY
    entity = BenUnit
    label = "Tenure type of the family's household"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit.value_from_first_person(
            benunit.members.household("tenure_type", period)
        )
