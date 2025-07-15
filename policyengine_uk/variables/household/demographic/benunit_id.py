from policyengine_uk.model_api import *


class benunit_id(Variable):
    value_type = int
    entity = ben_unit
    label = "ID for the family"
    definition_period = YEAR
