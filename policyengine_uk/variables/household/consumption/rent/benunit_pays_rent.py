from policyengine_uk.model_api import *


class benunit_is_rent_liable(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether the benefit unit is liable to pay rent"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        rent = benunit("benunit_rent", period)
        return rent > 0
