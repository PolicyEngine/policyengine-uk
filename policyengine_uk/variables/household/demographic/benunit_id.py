from policyengine_uk.model_api import *


class benunit_id(Variable):
    value_type = int
    entity = BenUnit
    label = "ID for the family"
    definition_period = YEAR
