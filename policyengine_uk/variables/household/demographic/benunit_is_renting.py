from policyengine_uk.model_api import *


class benunit_is_renting(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether this family is renting"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        tenure = benunit("benunit_tenure_type", period)
        tenures = tenure.possible_values
        RENT_TENURES = [
            tenures.RENT_PRIVATELY,
            tenures.RENT_FROM_COUNCIL,
            tenures.RENT_FROM_HA,
        ]
        return sum([tenure == tenure_type for tenure_type in RENT_TENURES]) > 0
